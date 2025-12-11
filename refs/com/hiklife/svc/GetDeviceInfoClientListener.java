package com.hiklife.svc;

import refs.com.hiklife.svc.core.protocol.baseinfo.DevicePacket;

public interface GetDeviceInfoClientListener {
  void onGetDeviceInfoError(String paramString);
  
  void onGetDeviceInfo(DevicePacket paramDevicePacket);
}


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/GetDeviceInfoClientListener.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */