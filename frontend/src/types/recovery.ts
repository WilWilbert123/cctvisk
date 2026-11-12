export interface RecoveryStepItem {
  step_number: number;
  title: string;
  description: string;
  warning?: string | null;
}

export interface ManufacturerRecoveryGuide {
  id?: string;
  manufacturer: string;
  display_name?: string;
  supported_models?: string[];
  official_tools: string[];
  official_support_info: string;
  physical_reset_procedure: string;
  default_network_behavior?: string;
  steps: RecoveryStepItem[] | string[];
  warnings: string[];
  security_recommendations?: string[];
}

export interface VaultStatus {
  has_credentials: boolean;
  username: string | null;
  updated_at: string | null;
  encryption_algorithm: string;
}

export interface RecoveryRecord {
  id: number;
  device_id: number;
  ip_address?: string;
  device_label?: string;
  manufacturer: string;
  model?: string | null;
  method_used: string;
  status: 'in_progress' | 'completed' | 'requires_support' | 'failed' | string;
  notes?: string | null;
  created_at: string;
}

export interface DeviceRecoveryContext {
  device_id: number;
  ip_address: string;
  label?: string | null;
  manufacturer: string;
  model?: string | null;
  admin_url?: string | null;
  guide: ManufacturerRecoveryGuide;
  vault_status: VaultStatus;
  history: RecoveryRecord[];
}

export interface SaveVaultCredentialsPayload {
  device_id: number;
  username: string;
  password?: string;
  port?: number;
  notes?: string;
  explicit_user_consent: boolean;
}
