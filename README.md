# project-continuity

Uma skill para trabalhar em **um mesmo projeto com modelos de IA diferentes** (Claude Code, Codex, Antigravity e outros) sem perder continuidade. O estado do projeto fica em arquivos dentro do repositório; o histórico do chat é apenas complemento. Quando a cota de um modelo está acabando, ele faz o handoff e o próximo assume exatamente de onde o anterior parou, manualmente ou por um supervisor automático.

O protocolo (`SKILL.md`, `PROTOCOL.md`) está em inglês para que modelos de qualquer fornecedor o sigam de forma uniforme. Os registros do projeto são escritos no idioma do projeto.

## Como funciona

| Modo | Quando usar | Resultado |
|---|---|---|
| `init` | Projeto novo, sem `.continuity/` | Cria registros, scripts, configuração e arquivos de entrada (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) |
| `continue` | Início de qualquer sessão, ou quando outro modelo assume | Lê o estado, checa a cota, envia um resumo de 5 linhas e retoma o trabalho |
| `checkpoint` | Durante o trabalho (automático) ou sob pedido | Atualiza LOG e HANDOFF em menos de um minuto |
| `handoff` | Cota no limiar, troca de modelo ou fim do trabalho | Estado `PAUSED`, próxima ação registrada, o modelo para |

Os modos são instruções em linguagem natural, não comandos de terminal: "use project-continuity init neste projeto", "continue", "handoff". Depois do `init`, o projeto leva o protocolo consigo (`.continuity/PROTOCOL.md` e os ponteiros), então qualquer ferramenta o segue mesmo sem a skill instalada.

### O que o `init` cria no projeto

```
AGENTS.md / CLAUDE.md / GEMINI.md   ponteiro curto para o protocolo (mesclado, nunca sobrescrito)
.continuity/
  PROTOCOL.md      regras: única fonte de verdade do protocolo (protocol_version no topo)
  CONTEXT.md       orientação estável: objetivo, escopo aprovado, quadro de tarefas, decisões
  HANDOFF.md       estado agora (ACTIVE/PAUSED), próxima ação, árvore de trabalho; sobrescrito
  LOG.md           histórico append-only e evidências
  QUOTA.md         como ler a cota restante em cada ferramenta
  config.json      limiar de cota, delegação e relay
  scripts/         quota_check.py, relay.py, claude_statusline.sh
  quota/ relay/    leituras de cota e logs do supervisor (local, fora do Git)
```

Cada fato vive em um único arquivo; os demais apontam para ele.

## Monitoramento de cota e handoff automático

O modelo verifica a cota restante ao iniciar, em cada checkpoint e antes de operações longas. Quando uma janela chega ao **limiar configurável** (padrão 10% restante), ele para e faz o handoff.

```bash
python3 .continuity/scripts/quota_check.py --tool claude-code
# exit 0 acima do limiar | 10 no limiar ou abaixo | 4 leitura antiga | 3 sem leitura
```

O limiar fica em `.continuity/config.json` (`handoff_threshold_percent`, com `thresholds` opcional por janela). Para mudar, peça "muda o limiar para 15%" ou edite o arquivo.

Nenhuma ferramenta entrega a cota ao modelo sozinha, então a leitura depende de cada uma:

| Ferramenta | Origem da leitura |
|---|---|
| Claude Code | Automática: `scripts/claude_statusline.sh` grava `rate_limits` da statusline em `.continuity/quota/claude-code.json` (precisa de login Pro/Max e `jq`) |
| Codex CLI | `/status` (janela de 5h e semanal); registrar com `--set-remaining` |
| Antigravity (`agy`) | `/usage` (alias `/quota`); registrar com `--set-remaining` |
| Gemini CLI | `/stats model`; registrar com `--used N --limit M` |
| Cursor | Só o dashboard; o usuário informa o número |

Se não houver leitura, o modelo registra "quota: indisponível" e faz checkpoints mais frequentes. Ele nunca estima percentuais. Mesmo com o limiar, a cota pode acabar no meio de uma operação, e por isso o checkpoint contínuo é a rede de segurança: a próxima ação já está salva antes de cada passo.

## Delegação para modelos menores

O modelo principal pode delegar trabalho limitado e de baixo risco (busca, leitura, edições mecânicas, boilerplate, testes de comportamento já especificado) a modelos mais baratos para economizar tokens. Decisões, arquitetura, mudanças sensíveis, revisão final e escrita dos registros ficam com o principal, que **verifica todo resultado** antes de aceitar. Configuração em `config.json` > `delegation` (`enabled`, `max_parallel`, `model_tiers`).

## Relay: revezamento automático entre CLIs (opcional)

`scripts/relay.py` é um supervisor que você roda no terminal. Ele abre um CLI por vez em modo não interativo com o prompt do `continue`, espera terminar, lê o `HANDOFF.md` e abre o próximo CLI disponível.

```bash
python3 .continuity/scripts/relay.py status        # CLIs encontrados, cota, estado do handoff
python3 .continuity/scripts/relay.py run --dry-run # mostra o próximo modelo sem executar
python3 .continuity/scripts/relay.py run           # inicia o loop
```

- **Desligado por padrão.** Só roda com `"relay": {"enabled": true}` em `config.json`, depois de você revisar o comando e as permissões de cada modelo.
- Pula CLIs que não existem no PATH e modelos cuja última leitura de cota recente está no limiar ou abaixo. Uma leitura antiga não bloqueia, porque a janela pode ter renovado, e o próprio modelo checa ao iniciar.
- Um modelo cortado por limite sem fazer handoff deixa o estado `ACTIVE`; o supervisor verifica que o processo terminou e o próximo modelo roda a recuperação, sem descartar nada.
- Para quando: o trabalho aprovado termina (`complete`), falta uma decisão humana (`needs-human`), nenhum modelo está disponível (mostra quando a janela mais próxima renova), não há progresso em sessões seguidas, ou o limite de sessões é atingido. **Nunca espera nem explora a renovação da cota.**
- Cada execução tem timeout, e processos travados são encerrados.
- Um modelo que passa a vez com `model-switch` (ou que bateu no limite, caiu ou travou) não é relançado em seguida. Se o log de uma sessão que falhou contém uma mensagem de limite de uso, o modelo fica em "descanso" por `stale_after_minutes` (é uma observação registrada na janela `relay_limit`, não uma estimativa).
- No modo headless o Claude Code provavelmente não alimenta a leitura de cota da statusline (não verificado); nesse caso o handoff acontece pelo corte por limite e pela recuperação, não pelo limiar.

Comandos padrão (verificar na versão instalada; as flags mudam):

| CLI | Comando |
|---|---|
| Claude Code | `claude -p "<prompt>" --allowedTools "Read,Edit,Write,Glob,Grep,Bash(git:*),Bash(python3 .continuity/scripts/quota_check.py:*),Bash(date:*)"` |
| Codex | `codex exec --sandbox workspace-write "<prompt>"` |
| Antigravity | `agy -p "<prompt>" --print-timeout 60m` |

**Atenção às permissões.** Sessões não interativas não podem pedir aprovação, então os comandos pré-autorizam só o necessário. Se o seu projeto precisa rodar testes, acrescente o comando de teste à lista. No Antigravity, as permissões em modo headless são inconsistentes nas versões atuais (concessões `command()` em `settings.json` podem ser ignoradas); veja `references/adapters.md`. Opções como `--dangerously-skip-permissions` nunca são usadas por padrão.

## Estrutura da skill

```
SKILL.md                   modos e regras inegociáveis
references/
  modes.md                 procedimento do init (continue/checkpoint/handoff vivem no PROTOCOL.md)
  records.md               contratos dos registros, limites de tamanho e rotação do LOG
  quota.md                 monitoramento de cota e limiar configurável
  adapters.md              ponteiros e comandos headless por ferramenta
assets/templates/          PROTOCOL, CONTEXT, HANDOFF, LOG, QUOTA, config.json, pointer e exemplos
scripts/                   quota_check.py, relay.py, claude_statusline.sh
tests/                     testes de quota_check.py e do relay (com CLIs falsos)
```

## Instalação

Coloque esta pasta onde a sua ferramenta procura skills (ou mantenha em um caminho conhecido e diga "leia `<caminho>/SKILL.md` e rode `init`"). Instale apenas com a sua autorização e verifique a documentação atual de cada ferramenta, já que os locais e a sintaxe mudam por versão.

## Testes

```bash
python3 -m unittest discover -s tests
```

Python 3 com biblioteca padrão, sem dependências. O relay roda em macOS e Linux.

### Teste com os CLIs reais

Os testes automáticos usam CLIs falsos. Para exercitar o relay com Claude Code, Codex e Antigravity de verdade, rode no Terminal:

```bash
bash scripts/smoke_test.sh            # cria ~/relay-teste com uma tarefa pequena aprovada
TWO_TASKS=1 bash scripts/smoke_test.sh ~/relay-troca   # 2 tarefas: força uma troca real de modelo (model-switch)
THRESHOLD=95 bash scripts/smoke_test.sh ~/outro-dir     # limiar configurável
```

Com `TWO_TASKS=1` o primeiro modelo faz a T1 e passa a vez com `model-switch`; o relay então lança **outro** CLI para a T2. O script também confere as versões instaladas e se as flags dos comandos existem.

O script mostra `status` e `--dry-run` e só executa o `run` (que usa a cota dos CLIs reais) depois da sua confirmação. No fim imprime o LOG, o HANDOFF e o resultado do teste da tarefa; se uma sessão falhar, veja `.continuity/relay/*.log` no projeto de teste.

## Limitações conhecidas

- A leitura de cota é automática apenas no Claude Code; nos demais depende de o modelo ou de você informar o número.
- A cota é da conta, não do projeto: um handoff por uma janela vale para todos os projetos que a usam.
- Os comandos headless e as flags de permissão vêm da documentação dos fornecedores em outubro de 2026 e precisam ser conferidos na sua versão. O Cursor não tem modo headless verificado e por isso não está no relay.
- Os testes automáticos do relay usam CLIs falsos. O teste real com Claude Code (uma tarefa) funcionou; a troca real entre dois CLIs ainda precisa ser rodada com `TWO_TASKS=1`.
- Os modelos não sabem a hora: o protocolo manda lerem `date`, e o comando do Claude libera `Bash(date:*)`.

## Histórico

A versão original da skill (v1) foi criada com o ChatGPT e revisada em outubro de 2026 com análise de um subagente especialista. A v2 acrescenta checkpoint contínuo, templates, monitoramento de cota configurável, delegação e o relay.
