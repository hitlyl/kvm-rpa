package com.hiklife.svc.core.protocol.handler;

import refs.com.hiklife.svc.core.protocol.security.SecurityType;

public interface ProtocolAuthEvent {
  void onRequireAuth(SecurityType.Type paramType);
  
  void onAuthSuccess();
  
  void onAuthFailed(String paramString);
}


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/handler/ProtocolAuthEvent.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */