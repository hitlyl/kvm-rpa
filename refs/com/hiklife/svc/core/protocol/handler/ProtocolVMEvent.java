package com.hiklife.svc.core.protocol.handler;

import refs.com.hiklife.svc.core.protocol.ProtocolContext;

public interface ProtocolVMEvent {
  void onVMReadStarting();
  
  void onVMReadEnd();
  
  void onVMWritStarting();
  
  void onVMWriteEnd();
  
  void onRefreshVMContext(ProtocolContext paramProtocolContext);
}


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/handler/ProtocolVMEvent.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */