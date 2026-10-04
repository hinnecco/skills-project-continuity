# project-continuity

**Português** | [English](README.en.md)

Uma skill para trabalhar em **um mesmo projeto com modelos de IA diferentes** (Claude Code, Codex, Antigravity, Gemini CLI, Cursor) sem perder continuidade. O estado do projeto fica em arquivos dentro do repositório; o histórico do chat é só complemento. Quando um modelo vai parar (cota no limiar, troca de ferramenta, fim do trabalho), ele faz o handoff e o próximo assume exatamente de onde o anterior parou.

O protocolo está em inglês para que modelos de qualquer fornecedor o sigam do mesmo jeito; os registros do projeto ficam no idioma do projeto.

## Núcleo (padrão): simples e sem permissões extras

Quatro modos, ditos em linguagem natural ("use project-continuity init neste projeto", "continue", "handoff"):

| Modo | Quando usar | Resultado |
|---|---|---|
| `init` | Projeto sem `.continuity/` | Cria os registros e os arquivos de entrada (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) |
| `continue` | Início de qualquer sessão, ou quando outro modelo assume | Lê o estado, checa a cota, manda um resumo de 5 linhas e retoma |
| `checkpoint` | Durante o trabalho ou sob pedido | Atualiza LOG e HANDOFF em menos de um minuto |
| `handoff` | Cota no limiar, troca de modelo ou fim | Estado `PAUSED`, próxima ação registrada, o modelo para |

O `init` cria no projeto:

```
AGENTS.md / CLAUDE.md / GEMINI.md   ponteiro curto para o protocolo (mesclado, nunca sobrescrito)
.continuity/
  PROTOCOL.md   as regras, a única fonte de verdade (leva o protocolo junto com o projeto)
  CONTEXT.md    orientação estável: objetivo, escopo aprovado, quadro de tarefas, decisões
  HANDOFF.md    estado agora (ACTIVE/PAUSED), próxima ação, árvore de trabalho; sobrescrito
  LOG.md        histórico append-only e evidências
  config.json   limiar de cota (padrão 10% restante)
```

Pontos importantes do protocolo:

- **Checkpoint contínuo.** O modelo grava a próxima ação antes de cada passo, então um corte por limite não perde o contexto. Um `HANDOFF` em `ACTIVE` significa que o modelo anterior não encerrou, e o próximo roda uma recuperação sem descartar nada.
- **Limiar de cota configurável.** O modelo só considera a cota que for real: o que a ferramenta mostra (`/status` no Codex, `/usage` no Antigravity e no Claude Code etc.), o que você disser, ou um aviso do provedor. Se não souber, registra "quota: unavailable" e faz checkpoints mais frequentes. Nunca inventa percentuais. No limiar, faz handoff.
- **Registro não é autorização.** O modelo só faz o que está no escopo aprovado ou o que você pedir agora.
- **Superpowers.** Se já existir no ambiente, o modelo usa as skills relevantes sem refazer etapas já concluídas; se não existir, segue normalmente e não instala nada.
- **Horários vêm de `date`**, porque modelos não sabem a hora.

## Extras (opcionais, desligados por padrão)

Automação que precisa de mais permissões. Ative só se quiser; detalhes em [`extras/README.md`](extras/README.md).

| Extra | O que faz | Precisa de |
|---|---|---|
| Leitor de cota | `quota_check.py` lê a última leitura por ferramenta e sinaliza o limiar; a statusline do Claude Code grava a leitura automaticamente | Python 3; no Claude Code, `jq`, login Pro/Max e editar `~/.claude/settings.json` |
| Delegação | O modelo principal passa tarefas rotineiras a modelos mais baratos e verifica os resultados | Harness com subagentes ou troca de modelo |
| Relay | `relay.py` abre Claude Code, Codex e Antigravity um depois do outro em modo headless | Permissões não interativas dos CLIs (ferramentas permitidas, sandbox) e um terminal aberto |

Estado de cada extra: o relay foi validado com Claude Code (2.1.289) e Codex (0.160.0) reais em um teste de duas tarefas com troca de modelo, e com CLIs falsos nos testes automáticos; o Antigravity não foi exercitado. Em sessões não interativas nenhum CLI conseguiu ler a própria cota, então ali o limiar não dispara; o relay troca de modelo por `model-switch`, `complete`, `needs-human` ou pela recuperação após um corte.

## Estrutura do repositório

```
SKILL.md                    modos e regras inegociáveis
references/                 modes.md (init), records.md (contratos dos registros), adapters.md (por ferramenta)
assets/templates/           PROTOCOL, CONTEXT, HANDOFF, LOG, config.json, pointer e exemplos
extras/                     scripts, tests, docs e config dos extras opcionais
```

## Instalação

Coloque esta pasta onde a sua ferramenta procura skills, ou mantenha em um caminho conhecido e diga "leia `<caminho>/SKILL.md` e rode `init`". Instale só com a sua autorização e confira a documentação atual de cada ferramenta.

## Testes

```bash
python3 -m unittest discover -s extras/tests
```

Biblioteca padrão do Python 3, sem dependências. Os testes cobrem os extras (leitor de cota e relay); o núcleo são só arquivos de texto.

## Limitações conhecidas

- A cota é da conta, não do projeto: um handoff por uma janela vale para todos os projetos que a usam.
- Os comandos headless e as flags dos extras vêm da documentação dos fornecedores em outubro de 2026 e precisam ser conferidos na versão instalada.
- Os modelos às vezes erram os horários mesmo com a regra do `date`.

## Histórico

A v1 foi criada com o ChatGPT. A v2 foi revisada com um subagente especialista e acrescentou checkpoint contínuo, templates, limiar de cota configurável, delegação e relay. A v3 separou o núcleo dos extras para reduzir a complexidade e as permissões necessárias.
