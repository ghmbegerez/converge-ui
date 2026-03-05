# CODA Vision Spec

## 1. Resumen

CODA es un sistema distribuido de creacion de software agentico.

Modelo base:
- `motor` (control, orquestacion, gobernanza, memoria decisional),
- `cliente` (interfaz de operador/desarrollador).

CODA se apoya en:
- `converge` como guardian de calidad evolutiva,
- `converge-orchestrator` como runtime de ejecucion paralela,
- `converge-ui` como control plane unificado.

## 2. Declaracion de vision

La creacion de software evoluciona de "escritura manual de codigo" a
"sistema de decisiones agenticas basadas en evidencia".

CODA busca:
1. Ejecutar miles de micro-decisiones en paralelo.
2. Mantener contexto de ejecucion limpio (task-local).
3. Maximizar informacion de decision (evidencia global).
4. Proteger el activo creado hoy y su evolucion futura.

## 3. Problema que resuelve

En escenarios de alto volumen:
- crece el retrabajo,
- se acumula deuda estructural,
- la gobernanza se vuelve reactiva,
- la velocidad local degrada salud global.

CODA resuelve esto combinando:
- pools de agentes especializados,
- intents pequeños y trazables,
- gates de gobernanza por riesgo,
- memoria de decisiones reusable.

## 4. Principios

1. Contexto cero para ejecutar; contexto total para decidir.
2. Ningun merge a main sin veredicto de gobernanza.
3. Todo cambio es un intent con evidencia.
4. Toda decision tiene trace_id y auditoria.
5. Fast-path para bajo riesgo; control reforzado para alto riesgo.
6. Arquitectura modular: API sobre API interna.

## 5. Modelo conceptual

### 5.1 Unidad minima
`Intent`: contrato de cambio con:
- objetivo,
- alcance,
- riesgo esperado,
- rollback,
- criterios de aceptacion,
- evidencia.

### 5.2 Agente
Ejecutor especializado por dominio (tests, refactor, bugfix, deps, docs, etc.).

### 5.3 Pool
Conjunto de agentes del mismo tipo con estrategia de asignacion (round-robin, score-based, risk-aware).

### 5.4 Decisión
Resultado verificable de un intent:
- `ALLOW`, `BLOCK`, `RETRY`, `REVIEW_REQUIRED`.

## 6. Arquitectura distribuida

## 6.1 Motor CODA
Servicios principales:
1. Intent Router: enruta intents a pools.
2. Agent Scheduler: asigna tareas y balancea carga.
3. Decision Fabric: consolida evidencia y pide veredicto a converge.
4. State & Memory: guarda estado operativo + dataset decisional.
5. Policy Runtime: aplica reglas dinámicas por riesgo/tenant.
6. Audit Bus: eventos estructurados y trazabilidad completa.

## 6.2 Cliente CODA
Funciones:
- crear/editar intents,
- lanzar swarms,
- observar progreso,
- aprobar excepciones,
- consultar explicaciones de decision,
- operar rollback.

## 6.3 Integracion de componentes existentes
- `converge`: risk/policy/health/compliance/audit.
- `converge-orchestrator`: panes/worktrees/hooks/merge lifecycle.
- `converge-ui`: frontend/control API para operar ambos.

## 7. Flujo de vida de un intent

1. Ingesta: cliente crea intent.
2. Enriquecimiento: se agrega contexto semantico y constraints.
3. Planificacion: scheduler asigna pool/agente.
4. Ejecucion: agente produce cambio en worktree aislado.
5. Pre-merge phase 1: `main -> worktree`.
6. Evaluacion: converge calcula riesgo/entropia/dano/veredicto.
7. Integracion phase 2: `worktree -> main` solo si ALLOW.
8. Cleanup + aprendizaje: se registra evidencia y resultado.

## 8. Contratos de datos minimos

### 8.1 Intent envelope
- `intent_id`
- `project_id`
- `agent_pool`
- `objective`
- `scope`
- `risk_profile`
- `acceptance_criteria`
- `rollback_plan`
- `trace_id`

### 8.2 Decision record
- `decision`
- `reasons`
- `risk_score`
- `damage_score`
- `entropy_delta`
- `propagation_score`
- `evidence_refs`
- `timestamp`

## 9. Gobernanza y seguridad

1. RBAC por rol (`viewer`, `operator`, `admin`).
2. Tenant isolation estricto.
3. API scopes por recurso/accion.
4. Auditoria de acceso (`access.granted`/`access.denied`).
5. Policy-as-code versionada.

## 10. Observabilidad y aprendizaje

KPIs base:
- P95 tiempo de decision por intent.
- Throughput de intents por pool.
- Tasa de bloqueo por perfil de riesgo.
- Entropia semanal (repo/change).
- Incidentes post-merge.

Dataset de aprendizaje:
- intent + contexto + decision + outcome.
- usado para calibrar umbrales y mejorar enrutamiento.

## 11. Modos operativos

1. Shadow mode: recomienda, no bloquea.
2. Guarded mode: bloquea alto riesgo, deja fast-path bajo riesgo.
3. Enforce mode: decisiones plenamente vinculantes.

## 12. Estrategia de rollout

Fase A (MVP):
- intents + pools + merge 2 fases + gate converge.

Fase B:
- multi-project/multi-tenant + hooks avanzados + dashboard operativo.

Fase C:
- aprendizaje continuo, auto-calibracion, escalado a miles de intents/agentes.

## 13. Criterios de exito

1. Menor retrabajo por conflictos.
2. Menor incident rate post-merge.
3. Entropia estable o decreciente.
4. Mayor throughput sin degradar salud del repo.
5. Trazabilidad total de decisiones.

## 14. Riesgos

1. Sobrebloqueo por policies conservadoras.
2. Complejidad operativa de swarms masivos.
3. Costo de observabilidad y storage de eventos.
4. Dependencia excesiva de automatismos sin calibracion.

Mitigacion:
- rollout gradual,
- shadow antes de enforce,
- revisiones semanales de calibracion,
- human override controlado y auditado.

## 15. Decisión

Construir CODA como sistema distribuido `motor + cliente` sobre converge y converge-orchestrator es correcto y viable.

No es solo automatizacion de codigo.
Es infraestructura de decisiones para creacion de software sostenible a escala.
