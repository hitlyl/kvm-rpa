package com.hiklife.svc.core.protocol.handler;

import org.apache.mina.core.session.IoSession;

public interface ProtocolConnectEvent {
  void onConnectSuccess(IoSession paramIoSession);
  
  void onConnectFailed();
  
  void onConnectClose(String paramString);
  
  void onInvalidRFBMessageException(Throwable paramThrowable);
  
  void onCaughtException(Throwable paramThrowable);
  
  void onAfterInitialisation();
}


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/handler/ProtocolConnectEvent.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */