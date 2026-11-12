import React from 'react';
import { Radio, Lock } from 'lucide-react';
import { Badge } from '../ui/Badge';

interface CameraStatusProps {
  isOnline: boolean;
  streamActive?: boolean;
  hasSavedCredentials?: boolean;
  onvifSupported?: boolean;
  rtspSupported?: boolean;
}

export const CameraStatus: React.FC<CameraStatusProps> = ({
  isOnline,
  streamActive = false,
  hasSavedCredentials = false,
  onvifSupported = false,
  rtspSupported = true,
}) => {
  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      <Badge variant={isOnline ? 'success' : 'danger'} dot>
        {isOnline ? 'Online' : 'Offline'}
      </Badge>

      {streamActive && (
        <Badge variant="info" className="animate-pulse">
          <Radio className="w-3 h-3 mr-1" />
          LIVE STREAM
        </Badge>
      )}

      {onvifSupported && <Badge variant="info">ONVIF</Badge>}
      {rtspSupported && <Badge variant="outline">RTSP</Badge>}

      {hasSavedCredentials && (
        <Badge variant="success" title="Encrypted credentials stored in Vault">
          <Lock className="w-3 h-3 mr-1" />
          Vault Ready
        </Badge>
      )}
    </div>
  );
};
