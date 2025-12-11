/*    */ package com.hiklife.svc.core.protocol.baseinfo;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class ChannelInfo
/*    */ {
/*    */   public static final int CHANNEL_STATE_OFFLINE = 0;
/*    */   public static final int CHANNEL_STATE_ONLINE = 1;
/*    */   public static final int CHANNEL_STATE_USE = 2;
/*    */   public static final int SOCKET_TYPE_SOCKET = 1;
/*    */   public static final int SOCKET_TYPE_SSL = 2;
/*    */   private int channelNo;
/*    */   private int socketType;
/*    */   private int channelState;
/*    */   private int deviceType;
/*    */   private String deviceId;
/*    */   private String deviceName;
/*    */   private String hardwareVer;
/*    */   private String softwareVer;
/*    */   
/*    */   public int getChannelNo() {
/* 26 */     return this.channelNo;
/*    */   }
/*    */   
/*    */   public void setChannelNo(int channelNo) {
/* 30 */     this.channelNo = channelNo;
/*    */   }
/*    */   
/*    */   public int getSocketType() {
/* 34 */     return this.socketType;
/*    */   }
/*    */   
/*    */   public void setSocketType(int socketType) {
/* 38 */     this.socketType = socketType;
/*    */   }
/*    */   
/*    */   public int getChannelState() {
/* 42 */     return this.channelState;
/*    */   }
/*    */   
/*    */   public void setChannelState(int channelState) {
/* 46 */     this.channelState = channelState;
/*    */   }
/*    */   
/*    */   public int getDeviceType() {
/* 50 */     return this.deviceType;
/*    */   }
/*    */   
/*    */   public void setDeviceType(int deviceType) {
/* 54 */     this.deviceType = deviceType;
/*    */   }
/*    */   
/*    */   public String getDeviceId() {
/* 58 */     return this.deviceId;
/*    */   }
/*    */   
/*    */   public void setDeviceId(String deviceId) {
/* 62 */     this.deviceId = deviceId;
/*    */   }
/*    */   
/*    */   public String getDeviceName() {
/* 66 */     return this.deviceName;
/*    */   }
/*    */   
/*    */   public void setDeviceName(String deviceName) {
/* 70 */     this.deviceName = deviceName;
/*    */   }
/*    */   
/*    */   public String getHardwareVer() {
/* 74 */     return this.hardwareVer;
/*    */   }
/*    */   
/*    */   public void setHardwareVer(String hardwareVer) {
/* 78 */     this.hardwareVer = hardwareVer;
/*    */   }
/*    */   
/*    */   public String getSoftwareVer() {
/* 82 */     return this.softwareVer;
/*    */   }
/*    */   
/*    */   public void setSoftwareVer(String softwareVer) {
/* 86 */     this.softwareVer = softwareVer;
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/baseinfo/ChannelInfo.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */