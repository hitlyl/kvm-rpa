package com.hiklife.svc.core.protocol.handler;

import refs.com.hiklife.svc.core.protocol.baseinfo.DevicePacket;
import refs.com.hiklife.svc.core.protocol.baseinfo.VersionPacket;

public interface ProtocolDeviceInfoEvent {
  void onGetDevice(DevicePacket paramDevicePacket);
  
  void onGetVersion(VersionPacket paramVersionPacket);
}


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/handler/ProtocolDeviceInfoEvent.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */