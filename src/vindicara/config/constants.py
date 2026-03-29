"""Named constants for Vindicara."""

# API
API_VERSION = "v1"
API_KEY_PREFIX = "vnd_"
API_KEY_HEADER = "X-Vindicara-Key"
REQUEST_ID_HEADER = "X-Request-ID"

# Policy evaluation
MAX_INPUT_LENGTH = 100_000
MAX_OUTPUT_LENGTH = 500_000
MAX_POLICY_RULES = 50
DEFAULT_POLICY_TIMEOUT_MS = 100

# Risk scoring
RISK_LOW = 0.0
RISK_MEDIUM = 0.4
RISK_HIGH = 0.7
RISK_CRITICAL = 0.9

# DynamoDB
TABLE_NAME_POLICIES = "vindicara-policies"
TABLE_NAME_EVALUATIONS = "vindicara-evaluations"
TABLE_NAME_API_KEYS = "vindicara-api-keys"

# S3
BUCKET_NAME_AUDIT = "vindicara-audit"

# EventBridge
EVENT_BUS_NAME = "vindicara-events"
EVENT_SOURCE = "vindicara.engine"

# Audit
AUDIT_EVENT_GUARD = "guard.evaluation"
AUDIT_EVENT_POLICY_CREATE = "policy.created"
AUDIT_EVENT_POLICY_UPDATE = "policy.updated"
