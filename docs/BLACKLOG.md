# HCC BLACKLOG — O que falta para o Hermes Command Center ficar 100% funcional e operar somente com dados reais

Data: 2026-04-20
Repositório: `Incavenuziano/hermes-command-center`
Escopo auditado: estado atual do frontend oficial servido em `8787/8788` e backend oficial já presente no repositório.

## Objetivo deste relatório

Este documento descreve, em profundidade, o que ainda falta para o Hermes Command Center (HCC):

1. ficar 100% funcional do ponto de vista de operador,
2. eliminar dependência de dados mockados/sintéticos no frontend,
3. refletir somente dados reais do runtime Hermes e de stores reais do próprio HCC,
4. reduzir divergência entre “backend já existe” e “UI ainda não usa”,
5. sair do estado híbrido atual para um estado de control plane realmente operacional.

Este relatório é deliberadamente prescritivo: não apenas lista gaps, mas organiza o backlog por domínio, severidade, impacto operacional, dependências e definição de pronto.

---

## Resumo executivo

O HCC atual já passou do estágio de protótipo estático. Ele possui:

- shell oficial em produção (`8787` local, `8788` Tailscale),
- backend real com contratos relevantes já expostos,
- várias superfícies já alimentadas por runtime Hermes real,
- validação prática em browser,
- correções recentes de runtime, CSP, hidratação e empacotamento de vendor assets.

Mesmo assim, ele ainda NÃO está “100% funcional” porque hoje opera em modo híbrido:

- algumas páginas usam dados reais no núcleo e mock nos detalhes;
- algumas telas têm backend real disponível, mas o frontend ainda renderiza placeholders;
- algumas ações visuais existem na UI, mas não estão conectadas aos endpoints mutadores reais;
- algumas visões continuam produzindo dados sintéticos no frontend (timers, sparklines artificiais, deltas fake, histórico fake, transcript fake);
- a navegação SPA ainda não está 100% sincronizada com pathname/deep-link do navegador.

Em termos práticos, faltam 5 frentes grandes:

1. eliminar dados mockados do frontend;
2. ligar todas as páginas aos endpoints reais já existentes;
3. fechar os gaps onde o backend ainda não expõe o contrato necessário;
4. transformar affordances visuais em controles reais e auditáveis;
5. endurecer comportamento de navegação, refresh, estados vazios, erros e streaming.

---

## Diagnóstico do estado atual

### Estado atual por categoria

#### Já existe e funciona de forma parcialmente real
- Dashboard
- Agentes
- Sessões / Conversar
- Atividade
- Usage
- Crons
- Doctor
- indicador de saúde básica do gateway no topo

#### Backend real já existe, mas frontend ainda não usa direito ou não usa
- Chat transcript / stream
- Memory
- Skills
- Files / Documents
- Profiles / Preferences
- Gateway / Channels
- Processes
- Terminal policy
- Audit / Events / Activity stream
- System info
- Cost controls / circuit breaker mutável
- Cron history / cron control

#### Backend real melhorou recentemente, mas o frontend oficial ainda não fechou o circuito
- Approvals agora entram em `/ops/overview`, mas o Dashboard ainda não consome a fila real na UI
- `system_health` agora entra em `/ops/overview`, mas o card do Dashboard ainda não deixou de ser parcialmente hardcoded
- `/ops/usage` agora expõe um panel shape compatível com a UI, mas o frontend ainda mantém complementos sintéticos
- `/runtime/cron/jobs` agora expõe `jobs` além de `items`, mas o detalhe da página de Crons ainda segue mockado
- `/health/doctor` já normaliza `warn/err`, mas a página Doctor ainda não consome processos e system info reais por completo

#### Ainda é placeholder puro no frontend
- Tarefas
- Calendário
- Integrações
- Database
- APIs
- Canais
- Hooks
- Preferências
- Tailscale
- Config

---

## Princípio alvo: “somente dados reais”

Para o HCC chegar ao estado correto, as seguintes regras devem passar a ser verdade:

1. Nenhuma página principal deve depender de arrays mockados hardcoded para o happy path.
2. Nenhum indicador operacional deve ser fabricado por `setInterval()` no frontend para simular atividade real.
3. Nenhuma ação crítica deve existir apenas como botão visual sem integração real.
4. Nenhuma página operacional deve usar `PlaceholderPage` quando já existe endpoint real compatível.
5. Toda tela deve ter:
   - estado loading,
   - estado success com dados reais,
   - estado empty com semântica clara,
   - estado degraded/error quando backend/runtime não responder.
6. Toda fonte real deve vir de:
   - runtime Hermes,
   - stores persistentes do HCC,
   - contratos HTTP explícitos já versionados.

---

## Gap estrutural central

O principal problema do HCC hoje não é ausência total de backend; é o descasamento entre três camadas:

1. `backend/routes/*` já expõe superfícies reais,
2. `frontend/hermes/data.js` só hidrata uma fração dessas superfícies,
3. várias páginas ainda renderizam estruturas antigas que nasceram como mock/prototype-first UI.

Ou seja:
- backend evoluiu mais rápido do que a integração real da UI;
- a UI oficial já parece produto, mas parte dela continua sendo simulação estética.

Isso faz com que o HCC hoje seja visualmente convincente, porém operacionalmente incompleto.

---

## Backlog mestre por área

# A. Shell, roteamento e comportamento global

## A1. Corrigir roteamento SPA por pathname/deep-link

### Problema
O frontend inicializa a página ativa com `localStorage` (`saved.active || 'dashboard'`) em vez de derivar o estado da rota do navegador. Isso significa que abrir `/agents`, `/cron`, `/doctor`, etc. diretamente pode renderizar a tela errada.

### Impacto
- deep-link não confiável,
- refresh pode voltar para página errada,
- compartilhamento de URLs perde valor operacional,
- prejudica uso real do HCC como control plane.

### O que falta
- mapa bidirecional `pathname <-> active key`;
- leitura da rota atual no boot;
- atualização de `history.pushState` ao navegar via sidebar/topbar;
- suporte a `popstate`;
- fallback consistente para rotas inválidas.

### Definição de pronto
- abrir `/agents` carrega Agentes;
- refresh em `/cron` continua em Crons;
- botão voltar/avançar funciona;
- URL da página sempre representa o estado atual.

## A2. Remover badges estáticos da navegação lateral

### Problema
Sidebar ainda usa badges hardcoded (`12`, `6`, `3`, `!`).

### Impacto
- sinalização operacional falsa,
- mina confiança do operador.

### O que falta
- derivar badges de stores reais:
  - activity count recente,
  - approvals pendentes,
  - sessões/agents/crons com estado crítico;
- ou remover completamente os badges até haver fonte real robusta.

### Definição de pronto
- nenhum badge é fake;
- badge ausente é preferível a badge inventado.

## A3. Estados globais reais de loading / empty / degraded

### Problema
A UI atual assume disponibilidade e shape correto em vários pontos.

### O que falta
- camada comum de fetch status;
- banners de runtime degradado;
- mensagens claras para backend indisponível, auth falha, stores vazios.

### Definição de pronto
- toda página principal possui estados explícitos e testados.

---

# B. Dashboard

## B1. Substituir feed “live activity” sintético por stream real

### Problema
O Dashboard ainda gera eventos sintéticos via timer no frontend.

### Backend relevante já existente
- `GET /ops/events`
- `GET /ops/activity`
- `GET /ops/stream`

### O que falta
- ligar Dashboard ao feed real;
- usar SSE real (`/ops/stream`) ou polling real controlado;
- remover templates artificiais do frontend;
- deduplicação por `event_id`;
- retenção visual com limite previsível.

### Definição de pronto
- nenhum novo evento do dashboard nasce de array fake local;
- tudo entra do event bus / derived state.

## B2. Approvals do dashboard devem consumir a fila real

### Problema
Dashboard ainda renderiza approvals mockados.

### Backend já existente
- `GET /ops/approvals`
- `POST /ops/approvals/resolve`
- approvals pendentes agora também entram em `GET /ops/overview`

### O que falta
- parar de depender do array mock local do Dashboard;
- consumir a fila real vinda de `/ops/overview` ou `/ops/approvals`;
- ações Approve / Deny reais;
- feedback visual após resolução;
- atualização via stream ou refetch;
- empty state quando não houver pendências.

### Definição de pronto
- painel mostra aprovações reais;
- decisões persistem e geram audit/evento.

## B3. Deltas e comparativos do dashboard precisam deixar de ser decorativos

### Problema
Textos como `+2 vs yesterday`, `+24% vs yesterday` ainda são sintéticos.

### O que falta
Há duas opções aceitáveis:
1. implementar comparativo real contra janela anterior; ou
2. remover completamente esse tipo de delta até existir base histórica consistente.

### Definição de pronto
- nenhum KPI exibe delta inventado.

## B4. Health card do dashboard precisa refletir fontes reais completas

### Problema
Partes do card ainda são hardcoded (`runtime online`, `event bus online`, `cost breaker healthy`).

### Backend já existente
- `/health`
- `/health/doctor`
- `/system/info`
- `/ops/usage`
- `/ops/gateway-runtime`
- `system_health` agora também entra em `/ops/overview`

### O que falta
- parar de usar partes hardcoded do card atual;
- decidir se a fonte canônica do card será `/ops/overview.system_health` ou composição explícita de `/system/info` + `/health` + `/ops/usage`;
- diferenciar `unknown`, `ok`, `warn`, `err`;
- não inferir “healthy” sem fonte real.

### Definição de pronto
- card inteiro vem de contratos reais, não de string fixa no JSX.

---

# C. Agentes

## C1. Enriquecer contrato real de agentes para eliminar campos fake

### Problema
A lista principal usa dados reais mapeados, mas detalhes ainda têm:
- created hardcoded,
- capabilities hardcoded,
- sparkline mockado,
- quick actions não conectadas.

### O que falta
No backend/runtime:
- created_at / registered_at do agente;
- capabilities reais ou flags reais do agente;
- métricas históricas reais (se a UI insistir em sparkline);
- relação de sessões recentes limpa.

No frontend:
- parar de preencher com defaults narrativos;
- mostrar `unknown` quando a fonte não existir.

### Definição de pronto
- página de agentes não contém detalhe inventado.

## C2. Quick actions reais para agentes

### Problema
Botões como Kill / Pause / Open chat são em grande parte affordances visuais.

### O que falta
- contrato explícito de ação por agente, se suportado;
- ou remover botões que ainda não têm operação real.

### Definição de pronto
- todo botão faz algo real e auditável, ou não existe.

---

# D. Sessões e Conversar

## D1. Trocar transcript mockado por transcript real

### Problema
A lista de sessões é parcialmente real, mas o painel de conversa ainda usa `data.transcript` mockado.

### Backend já existente
- `GET /ops/chat/transcript?session_id=...`
- `GET /ops/chat/stream?session_id=...`

### O que falta
- carregar transcript real por sessão selecionada;
- associar troca de sessão à recarga do painel;
- remover mensagens mockadas hardcoded;
- ligar streaming incremental ao painel.

### Definição de pronto
- selecionar uma sessão mostra sua transcrição real;
- novas mensagens entram pelo stream real.

## D2. Sessão detalhada precisa usar endpoint próprio

### Backend já existente
- `GET /ops/session?session_id=...`

### O que falta
- usar esse contrato para metadata do painel;
- exibir started_at, updated_at, model, platform, contagens, custos e tokens do backend;
- não derivar tudo por heurística local.

## D3. Implementar estados empty/degraded por sessão

### Problema
Se a sessão não tiver transcript, a UI precisa diferenciar:
- sessão sem mensagens,
- sessão inexistente,
- sessão ainda carregando,
- stream desconectado.

### Definição de pronto
- esses 4 cenários aparecem corretamente e sem ambiguidades.

---

# E. Atividade

## E1. Atividade deve consumir `/ops/activity` de verdade

### Problema
A tela de Atividade ainda está só parcialmente alinhada e o Dashboard injeta eventos locais sintéticos.

### O que falta
- Activity page passar a usar apenas feed real;
- filtros reais por prefixo/tipo;
- detail pane refletir payload real do evento;
- integração opcional com `/ops/stream`.

### Definição de pronto
- Activity vira canônica para timeline operacional real.

## E2. Drill-down do evento deve ser estruturado, não artificial

### Problema
O detail card ainda constrói parte do payload no frontend.

### O que falta
- exibir `kind`, `source`, `event_id`, `at`, payload real cru formatado;
- melhorar legibilidade sem inventar campos.

---

# F. Usage / custos / governança

## F1. Remover séries horárias sintéticas

### Problema
A série “hourly burn” ainda é sintetizada no frontend quando não existe série real pronta. O backend já passou a expor um panel shape mais amigável para Usage, mas ainda não fornece uma série temporal canônica.

### O que falta
Duas rotas possíveis:
1. adicionar série temporal real no backend; ou
2. remover o gráfico até existir dados reais confiáveis.

Observação:
- o panel shape recente em `/ops/usage` reduz o trabalho de adaptação no frontend para `today`, `breaker` e `agents`, mas não resolve o problema da série horária.

### Definição de pronto
- nenhum gráfico temporal usa dados fictícios.

## F2. Breaker editável precisa operar de forma real

### Backend já existente
- `POST /ops/costs/circuit-breaker`

### O que falta
- formulário ligado ao backend;
- optimistic update ou refetch;
- validação de input;
- erro/sucesso explícito;
- refletir thresholds reais retornados pelo backend.

### Definição de pronto
- editar breaker muda store real e volta corretamente para a UI.

## F3. Comparativos e request counts precisam ser reais

### Problema
Vários números auxiliares ainda são decorativos. O backend recente melhorou o shape de `today`/`breaker`/`agents`, mas ainda há campos que continuam sintéticos ou aproximados no frontend.

### O que falta
- request count real do período;
- comparativo real com janela anterior, se desejado;
- ou remoção dos adornos sintéticos;
- revisar o uso de fallback para `requests` no panel shape e substituir por métrica canônica quando ela existir.

---

# G. Crons

## G1. Detalhe de cron deve usar histórico real

### Backend já existente
- `GET /ops/cron/history`
- `GET /ops/cron/jobs`
- `GET /runtime/cron/jobs`
- `/runtime/cron/jobs` agora expõe `jobs` além de `items`

### Problema
A lista principal é real e o shape ficou mais amigável para o frontend, mas histórico e output continuam mockados.

### O que falta
- puxar histórico real por `job_id`;
- substituir tabela fake de runs;
- expor output/log real por execução, se backend ainda não expõe, criar endpoint específico;
- refletir `enabled`, `last_status`, `last_run_at`, `next_run_at` reais em toda a tela.

### Definição de pronto
- detalhe de cron é totalmente derivado do runtime real.

## G2. Ações Run/Pause/Resume precisam ser reais

### Backend já existente
- `POST /ops/cron/control`

### O que falta
- ligar botões ao endpoint;
- feedback de loading, sucesso, erro;
- refresh automático da linha e do detalhe;
- audit trail e event emission refletidos na UI.

### Definição de pronto
- o operador controla cron via HCC de verdade.

---

# H. Memory

## H1. Ligar a página de memória ao backend real

### Backend já existente
- `GET /ops/memory`

### Problema
Página atual ainda usa mock local.

### O que falta
- consumir `counts` e `items` reais;
- ajustar shape do frontend para `id`, `scope`, `text`, `preview`, `updated_at` reais;
- empty state quando não houver itens.

### Definição de pronto
- lista e detalhe refletem `memory.json`/fonte real do Hermes.

## H2. Definir se memória será read-only ou mutável no HCC

### Falta de produto/arquitetura
Hoje não está claro se o HCC deve:
- apenas inspecionar memória,
- ou permitir editar/apagar.

### O que falta
- decisão explícita;
- se for mutável, contratos de escrita seguros e auditáveis.

---

# I. Documents / Files

## I1. Ligar documentos ao backend real

### Backend já existente
- `GET /ops/files`

### Problema
Página ainda usa mock.

### O que falta
- consumir `root`, `count`, `items` reais;
- mapear `size_bytes` e `preview` reais;
- ordenar, paginar e filtrar;
- representar texto grande sem travar a UI.

### Definição de pronto
- a lista de documentos é uma visão real da workspace do Hermes/HCC.

## I2. Preview de arquivo precisa de contrato real mais rico

### Gap provável de backend
Hoje `files_summary()` entrega preview curto. Para uma UX realmente funcional, provavelmente faltará:
- endpoint de detalhe do arquivo;
- endpoint de download;
- distinção texto/binário;
- metadados de mtime reais.

### Definição de pronto
- clicar em arquivo mostra preview real, não texto sintético.

---

# J. Skills

## J1. Substituir placeholder por página real de skills

### Backend já existente
- `GET /ops/skills`
- superfícies de design advisor relacionadas

### O que falta
- página listando skills reais instaladas;
- preview do `SKILL.md`;
- filtros por categoria/origem;
- empty state; optionally integração futura com install/update.

### Definição de pronto
- operador consegue inspecionar skills reais pelo HCC.

---

# K. Channels / Gateway / Preferences / Profiles

## K1. Canais precisa sair de placeholder

### Backend já existente
- `GET /ops/gateway`

### O que falta
- renderizar gateway status real;
- listar canais reais;
- platform, label, delivery_state reais;
- estados secretos apenas redigidos, nunca expostos.

### Definição de pronto
- página Canais vira painel real do gateway.

## K2. Preferências / Profiles precisa sair de placeholder

### Backend já existente
- `GET /ops/profiles`

### O que falta
- listar profiles reais;
- indicar active_profile_id real;
- campos reais de sensibilidade/reauth;
- definir se haverá troca de perfil via UI.

### Definição de pronto
- página reflete profiles reais e não hint estático.

---

# L. Doctor

## L1. Doctor precisa consumir `/system/info` real

### Problema
Os checks já estão reais e o backend recente já normaliza melhor os status (`warn`/`err`). Mesmo assim, o painel “System info” ainda não é derivado do contrato correto.

### Backend já existente
- `/system/info`
- `/health`
- `/health/doctor`

### O que falta
- montar o bloco de system info a partir do payload real;
- refletir environment, bind, transport, auth_mode, secret storage e security posture reais.

### Definição de pronto
- Doctor não repete campos fake do dashboard; usa fontes reais apropriadas.

## L2. Doctor precisa consumir `/ops/processes` real no painel de processos

### Problema
Painel de processos ainda usa mock.

### Backend já existente
- `GET /ops/processes`
- detalhe de processo
- controles de processo

### O que falta
- listar processos reais;
- estado/pid/cwd/comando/session_key reais;
- eventualmente ligar inspect/kill/control.

### Definição de pronto
- Processes no Doctor refletem runtime real.

## L3. Re-run diagnostics precisa deixar de ser visual

### O que falta
- ou implementar ação real de reexecução;
- ou remover o botão até existir operação real.

---

# M. Terminal

## M1. Terminal atual é totalmente simulado

### Backend real relacionado já existe
- `/ops/terminal-policy`
- `/ops/read-only`
- `/ops/processes`
- `/ops/processes/control`

### Problema
A página mostra pseudo-terminal animado e mensagens sintéticas.

### O que falta
Decisão de produto:
1. terminal read-only real com stream de processos/logs; ou
2. painel de policy/guardrails + ações controladas; ou
3. remover a estética de terminal simulado.

### Recomendação
Para segurança e coerência com o projeto, o caminho melhor parece ser:
- não emular shell fake;
- mostrar policy real, processos reais, ações permitidas reais.

### Definição de pronto
- não existe texto fingindo terminal sem fonte real correspondente.

---

# N. Logs

## N1. Trocar log stream sintético por feed real

### Backend já existente
- `/ops/events`
- `/ops/activity`
- `/ops/audit`
- `/ops/stream`

### Problema
Página de logs ainda gera entradas artificiais.

### O que falta
- consolidar visão de logs reais;
- decidir se a fonte será event bus, audit log, ou ambas com tabs;
- filtros reais por nível/tipo/origem.

### Definição de pronto
- Logs deixa de ser demo animada e vira observabilidade útil.

---

# O. Placeholder pages que precisam virar páginas reais

As seguintes páginas ainda não são “funcionais” e precisam sair de `PlaceholderPage`:

## O1. Tarefas
Falta:
- decidir fonte real (issues, backlog local, queue interna, ou Linear/GitHub Issues);
- contrato backend e UI de list/detail/action.

## O2. Calendário
Falta:
- fonte real de agenda/cron/timeline;
- se não houver produto definido, melhor esconder do shell do que manter placeholder permanente.

## O3. Integrações
Falta:
- contrato de integrações reais (Monday, SALIC, Compras.gov, etc.);
- estado/config/health por integração.

## O4. Database
Falta:
- definir escopo seguro de inspeção SQLite;
- nunca virar console arbitrário de SQL sem guardrails.

## O5. APIs
Falta:
- catálogo real de endpoints / connectors / webhook consumers / upstream health.

## O6. Hooks
Falta:
- representação real de hooks, políticas e auditoria.

## O7. Tailscale
Falta:
- surface real de bind/posture/exposição/URLs/risco, idealmente derivada de config/system info.

## O8. Config
Falta:
- leitura real de configuração sanitizada;
- separação entre valores visíveis e secrets redigidos;
- eventual edição guardada e auditável, se permitida.

### Definição de pronto para placeholders
- página real com dados reais; ou
- página removida da navegação até existir implementação real.

---

# P. Backend gaps que ainda precisam existir para eliminar mocks restantes

Mesmo com muito backend já presente, para eliminar 100% dos mocks ainda faltarão alguns contratos ou enriquecimentos:

## P1. Endpoint de detalhe/output de cron run
Necessário para substituir “Last output” fake.

## P2. Série temporal real para Usage
Necessária se o gráfico horário continuar existindo.

## P3. Endpoint de detalhe/download de arquivo
Necessário para Documents realmente útil.

## P4. Contrato canônico de agent detail
Hoje há overview resumido, mas não um detail robusto para eliminar campos inventados.

## P5. Contrato canônico para actions de agent
Kill/pause/open-chat precisam de backend explícito ou devem sair da UI.

## P6. Possível endpoint de diagnostics rerun
Se o botão permanecer.

## P7. Event/log stream mais canônico para página de Logs
Para não misturar audit/events arbitrariamente no frontend.

---

# Q. Remoções necessárias (dívida de mock que não deve sobreviver)

Para “somente dados reais” não basta adicionar backend; também é preciso remover simulação residual.

## Q1. Remover timers que fabricam atividade
- Dashboard live activity fake
- Logs fake
- Terminal fake

## Q2. Remover sparklines artificiais se não houver série real
- Agents detail
- Usage fallback synthetic chart

## Q3. Remover contadores e deltas decorativos
- sidebar badges fake
- “vs yesterday” fake
- subtítulos inventados tipo “1 disabled” quando não forem derivados

## Q4. Remover detalhes fixos de narrativa
- created hardcoded de agentes
- capabilities inventadas
- transcript hardcoded
- cron history/output hardcoded

---

# R. Funcionalidade real de controles operacionais

Para ser 100% funcional, o HCC não pode ser só leitura bonita; ele precisa concluir o ciclo de ação com segurança.

## R1. Ações reais com auditoria
Toda ação importante deve:
- chamar endpoint real,
- registrar audit log,
- gerar evento para stream,
- refletir novo estado na UI.

### Ações prioritárias
- approvals resolve
- cron control
- process kill/control
- read-only toggle
- panic stop
- cost breaker update

## R2. UX de mutação robusta
Toda mutação precisa ter:
- loading state,
- disabled state enquanto envia,
- sucesso visível,
- erro visível,
- rollback ou refetch consistente.

---

# S. Segurança e consistência operacional

## S1. Não exibir controles não implementados
Botão falso em control plane é pior que ausência de botão.

## S2. Diferenciar “sem dado” de “sem integração” de “erro”
Esses três estados precisam ser semanticamente distintos.

## S3. Não inferir saúde sem fonte real
“healthy”, “online”, “ok” só quando vier de source real.

## S4. Sanitização consistente nas páginas de knowledge/config/gateway
Tudo que envolver caminhos, tokens, config ou secrets precisa ser redigido corretamente.

---

# T. Observabilidade do próprio HCC

## T1. Métricas internas do frontend
Faltam sinais práticos para operar a própria UI:
- última atualização por página;
- se a página está usando fallback;
- se stream está conectado ou degradado;
- request latency por surface.

## T2. Telemetria de erro do frontend
Hoje erros de runtime precisam ser vistos pelo console manual. Falta:
- surface de erro do frontend;
- event emission interna para falhas de hidratação/render.

---

# U. Ordem recomendada de execução para fechar o backlog

## Fase 1 — Remover o que é mais enganoso
1. corrigir pathname/deep-link SPA;
2. remover activity/logs/terminal sintéticos;
3. ligar approvals reais;
4. ligar transcript/stream reais;
5. ligar processes reais no Doctor.

## Fase 2 — Trocar placeholders por superfícies já suportadas pelo backend
6. Memory;
7. Documents/Files;
8. Skills;
9. Channels/Gateway;
10. Preferences/Profiles.

## Fase 3 — Fechar detalhes operacionais de controle
11. cron history/output/control reais;
12. cost breaker real completo;
13. process control real completo;
14. read-only / panic stop expostos corretamente na UI.

## Fase 4 — Fechar contratos ausentes
15. agent detail canônico;
16. file detail/download;
17. usage time-series real;
18. diagnostics rerun, se permanecer.

## Fase 5 — Limpeza final para “somente dados reais”
19. eliminar todo hardcoded remanescente de narrativa operacional;
20. remover placeholders restantes da navegação ou implementá-los de verdade;
21. revisar badges, deltas, chips e labels para garantir fonte real.

---

## Critério objetivo de “100% funcional”

O HCC só deve ser considerado 100% funcional quando TODOS os critérios abaixo forem verdadeiros:

1. Toda página visível no menu tem implementação real ou foi removida do menu.
2. Nenhuma página principal depende de arrays mockados para seu fluxo principal.
3. Nenhum dado operacional é gerado artificialmente no frontend por timer/simulação.
4. Todos os botões relevantes executam ações reais ou não existem.
5. Dashboard, Agents, Sessions, Chat, Activity, Usage, Cron, Doctor, Memory, Documents, Skills, Channels, Preferences, Logs e Terminal usam somente contratos reais.
6. Deep-link e refresh funcionam corretamente por pathname.
7. Estados loading/empty/error/degraded existem em todas as telas principais.
8. Toda mutação relevante gera efeito real, feedback visual e trilha de auditoria.
9. Nenhuma métrica ou badge importante é inventada.
10. O operador consegue confiar que a tela representa o estado real do sistema.

---

## Matriz final de status atual

### Híbridas (usar backend real + ainda contêm mock)
- Dashboard
- Agentes
- Sessões
- Conversar
- Atividade
- Usage
- Crons
- Doctor

### Backend pronto mas UI ainda não integrada
- Approvals
- Chat transcript/stream
- Memory
- Skills
- Files/Documents
- Profiles
- Gateway/Channels
- Processes
- Terminal policy
- Cost breaker mutation
- Cron history/control
- System info completo

### Placeholder puro
- Tarefas
- Calendário
- Integrações
- Database
- APIs
- Hooks
- Tailscale
- Config

---

## Recomendação final

A prioridade correta não é “criar mais páginas”; é terminar a transformação do HCC de UI demonstrativa híbrida para control plane verdadeiro.

Em termos de ROI operacional, a sequência mais importante é:

1. transcript real,
2. approvals reais,
3. activity/logs reais,
4. doctor/processes reais,
5. memory/files/profiles/gateway reais,
6. cron history/control reais,
7. remoção definitiva de todo mock remanescente.

Se essa sequência for cumprida, o HCC sai do estágio “bonito e promissor” para “confiável como centro operacional do Hermes”.
