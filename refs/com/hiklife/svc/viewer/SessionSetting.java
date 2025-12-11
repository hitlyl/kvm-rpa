package com.hiklife.svc.viewer;

import refs.com.hiklife.svc.core.protocol.normal.VideoParamPacket;

public interface SessionSetting {
  void writeMouseTypeRequest();
  
  void writeMouseType(int paramInt);
  
  void writeMouseTypeABS();
  
  void writeMouseTypeREL();
  
  void writeVideoParamRequest();
  
  void writeVideoParam(VideoParamPacket paramVideoParamPacket);
  
  void writeAudioParamRequest();
  
  void writeAudioParam(boolean paramBoolean);
}


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/viewer/SessionSetting.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */