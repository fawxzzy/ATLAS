export const ATLAS_ENV_CONTRACT_VERSION = "atlas.env.v1" as const;
export const ATLAS_APP_REGISTRATION_CONTRACT_VERSION =
  "atlas.app-registration.v1" as const;
export const ATLAS_HEALTH_CONTRACT_VERSION = "atlas.health.v1" as const;
export const ATLAS_EVENT_CONTRACT_VERSION = "atlas.event.v1" as const;
export const ATLAS_RECEIPT_CONTRACT_VERSION = "atlas.receipt.v1" as const;
export const ATLAS_COMPONENT_MANIFEST_CONTRACT_VERSION =
  "atlas.component-manifest.v2" as const;
export const ATLAS_JOB_ENVELOPE_CONTRACT_VERSION =
  "atlas.job-envelope.v2" as const;
export const ATLAS_EXECUTION_RECEIPT_CONTRACT_VERSION =
  "atlas.execution-receipt.v2" as const;
export const ATLAS_CONTEXT_PACKET_CONTRACT_VERSION = "atlas.context-packet.v2" as const;
export const ATLAS_EVIDENCE_BUNDLE_CONTRACT_VERSION = "atlas.evidence-bundle.v2" as const;
export const ATLAS_APPROVAL_RECORD_CONTRACT_VERSION = "atlas.approval-record.v2" as const;
export const ATLAS_WORKER_LEASE_CONTRACT_VERSION = "atlas.worker-lease.v2" as const;
export const ATLAS_CARD_RECORD_CONTRACT_VERSION = "atlas.card-record.v2" as const;
export const ATLAS_BOARD_EVENT_CONTRACT_VERSION = "atlas.board-event.v2" as const;

export const ATLAS_CONTRACT_VERSIONS = [
  ATLAS_ENV_CONTRACT_VERSION,
  ATLAS_APP_REGISTRATION_CONTRACT_VERSION,
  ATLAS_HEALTH_CONTRACT_VERSION,
  ATLAS_EVENT_CONTRACT_VERSION,
  ATLAS_RECEIPT_CONTRACT_VERSION,
  ATLAS_COMPONENT_MANIFEST_CONTRACT_VERSION,
  ATLAS_JOB_ENVELOPE_CONTRACT_VERSION,
  ATLAS_EXECUTION_RECEIPT_CONTRACT_VERSION,
  ATLAS_CONTEXT_PACKET_CONTRACT_VERSION,
  ATLAS_EVIDENCE_BUNDLE_CONTRACT_VERSION,
  ATLAS_APPROVAL_RECORD_CONTRACT_VERSION,
  ATLAS_WORKER_LEASE_CONTRACT_VERSION,
  ATLAS_CARD_RECORD_CONTRACT_VERSION,
  ATLAS_BOARD_EVENT_CONTRACT_VERSION,
] as const;

export const ATLAS_ENVIRONMENTS = [
  "local",
  "preview",
  "production",
  "ci",
  "test",
] as const;

export const ATLAS_REPO_CLASSES = [
  "stack",
  "application",
  "governance-runtime",
  "local-operator",
  "workflow-operator",
  "demo",
  "incubating",
  "legacy",
  "archive",
  "quarantined",
] as const;

export const ATLAS_REPO_STATUSES = [
  "active",
  "managed",
  "unmanaged",
  "verified",
  "incubating",
  "demo",
  "legacy",
  "archived",
  "quarantined",
] as const;

export const ATLAS_HEALTH_STATUSES = [
  "ok",
  "degraded",
  "failing",
  "unknown",
] as const;

export const ATLAS_RECEIPT_STATUSES = [
  "accepted",
  "rejected",
  "passed",
  "failed",
  "skipped",
  "warning",
] as const;

export const ATLAS_EVENT_PRODUCER_KINDS = [
  "wrapper",
  "native_hook",
  "git_hook",
  "ci",
  "service",
  "manual",
  "test",
  "browser",
  "worker",
] as const;

export const ATLAS_EVENT_LIFECYCLE_TYPES = [
  "session_start",
  "task_start",
  "pre_command",
  "post_command",
  "validation_complete",
  "export_complete",
  "session_stop",
] as const;

export const ATLAS_SCHEMA_PATHS = {
  [ATLAS_ENV_CONTRACT_VERSION]:
    "schemas/atlas.env.v1.schema.json",
  [ATLAS_APP_REGISTRATION_CONTRACT_VERSION]:
    "schemas/atlas.app-registration.v1.schema.json",
  [ATLAS_HEALTH_CONTRACT_VERSION]:
    "schemas/atlas.health.v1.schema.json",
  [ATLAS_EVENT_CONTRACT_VERSION]:
    "schemas/atlas.event.v1.schema.json",
  [ATLAS_RECEIPT_CONTRACT_VERSION]:
    "schemas/atlas.receipt.v1.schema.json",
  [ATLAS_COMPONENT_MANIFEST_CONTRACT_VERSION]:
    "schemas/atlas.component-manifest.v2.schema.json",
  [ATLAS_JOB_ENVELOPE_CONTRACT_VERSION]:
    "schemas/atlas.job-envelope.v2.schema.json",
  [ATLAS_EXECUTION_RECEIPT_CONTRACT_VERSION]:
    "schemas/atlas.execution-receipt.v2.schema.json",
  [ATLAS_CONTEXT_PACKET_CONTRACT_VERSION]: "schemas/atlas.context-packet.v2.schema.json",
  [ATLAS_EVIDENCE_BUNDLE_CONTRACT_VERSION]: "schemas/atlas.evidence-bundle.v2.schema.json",
  [ATLAS_APPROVAL_RECORD_CONTRACT_VERSION]: "schemas/atlas.approval-record.v2.schema.json",
  [ATLAS_WORKER_LEASE_CONTRACT_VERSION]: "schemas/atlas.worker-lease.v2.schema.json",
  [ATLAS_CARD_RECORD_CONTRACT_VERSION]: "schemas/atlas.card-record.v2.schema.json",
  [ATLAS_BOARD_EVENT_CONTRACT_VERSION]: "schemas/atlas.board-event.v2.schema.json",
} as const;

export type AtlasContractVersion = (typeof ATLAS_CONTRACT_VERSIONS)[number];
export type AtlasEnvironment = (typeof ATLAS_ENVIRONMENTS)[number];
export type AtlasRepoClass = (typeof ATLAS_REPO_CLASSES)[number];
export type AtlasRepoStatus = (typeof ATLAS_REPO_STATUSES)[number];
export type AtlasHealthStatus = (typeof ATLAS_HEALTH_STATUSES)[number];
export type AtlasReceiptStatus = (typeof ATLAS_RECEIPT_STATUSES)[number];
export type AtlasEventProducerKind =
  (typeof ATLAS_EVENT_PRODUCER_KINDS)[number];
export type AtlasLifecycleEventType =
  (typeof ATLAS_EVENT_LIFECYCLE_TYPES)[number];
