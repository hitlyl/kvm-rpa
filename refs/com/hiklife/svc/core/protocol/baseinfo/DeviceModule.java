/*     */ package com.hiklife.svc.core.protocol.baseinfo;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ public class DeviceModule
/*     */ {
/*     */   private byte deviceType;
/*     */   private String deviceTypeStr;
/*     */   private String deviceId;
/*     */   private String deviceName;
/*     */   private String hardwareVer;
/*     */   private String softwareVer;
/*     */   @Deprecated
/*     */   private byte cascadeMode;
/*     */   private byte socketType;
/*     */   private byte channelNumber;
/*     */   private byte[] channelsState;
/*     */   private byte[] path;
/*     */   
/*     */   public byte getDeviceType() {
/*  50 */     return this.deviceType;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setDeviceType(byte deviceType) {
/*  59 */     this.deviceType = deviceType;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public String getDeviceTypeStr() {
/*  68 */     return this.deviceTypeStr;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setDeviceTypeStr(String deviceTypeStr) {
/*  77 */     this.deviceTypeStr = deviceTypeStr;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public String getDeviceId() {
/*  86 */     return this.deviceId;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setDeviceId(String deviceId) {
/*  95 */     this.deviceId = deviceId;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public String getDeviceName() {
/* 104 */     return this.deviceName;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setDeviceName(String deviceName) {
/* 113 */     this.deviceName = deviceName;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public String getHardwareVer() {
/* 122 */     return this.hardwareVer;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setHardwareVer(String hardwareVer) {
/* 131 */     this.hardwareVer = hardwareVer;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public String getSoftwareVer() {
/* 140 */     return this.softwareVer;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setSoftwareVer(String softwareVer) {
/* 149 */     this.softwareVer = softwareVer;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public byte getCascadeMode() {
/* 158 */     return this.cascadeMode;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setCascadeMode(byte cascadeMode) {
/* 167 */     this.cascadeMode = cascadeMode;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public byte getSocketType() {
/* 176 */     return this.socketType;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setSocketType(byte socketType) {
/* 185 */     this.socketType = socketType;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public byte getChannelNumber() {
/* 194 */     return this.channelNumber;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setChannelNumber(byte channelNumber) {
/* 203 */     this.channelNumber = channelNumber;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public byte[] getChannelsState() {
/* 212 */     return this.channelsState;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setChannelsState(byte[] channelsState) {
/* 221 */     this.channelsState = channelsState;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public byte[] getPath() {
/* 230 */     return this.path;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setPath(byte[] path) {
/* 239 */     this.path = path;
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/baseinfo/DeviceModule.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */