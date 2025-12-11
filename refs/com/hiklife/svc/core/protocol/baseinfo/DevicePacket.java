/*     */ package com.hiklife.svc.core.protocol.baseinfo;
/*     */ import java.util.ArrayList;
/*     */ import java.util.List;

import refs.com.hiklife.svc.core.protocol.InvalidRFBMessageException;
import refs.com.hiklife.svc.core.protocol.baseinfo.ChannelInfo;
import refs.com.hiklife.svc.core.protocol.baseinfo.DeviceModule;
import refs.com.hiklife.svc.util.HexUtils;
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
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ public class DevicePacket
/*     */ {
/*     */   public static final int VERSION_LENGTH = 12;
/*     */   private static final int DEVICE_HEADER_LENGTH = 41;
/*     */   private static final int DEVICE_BODY_UNIT_LENGTH = 133;
/*     */   private static final int DEVICE_HEADER_DEVICE_TYPE_POS = 21;
/*     */   public static final int DEVICE_TYPE_EV5000 = 18;
/*     */   public static final int DEVICE_TYPE_RCM101 = 66;
/*     */   public static final int DEVICE_TYPE_EV6000A = 61;
/*     */   public static final int DEV_TYPE_EV4000A = 17;
/*     */   private String deviceType;
/*     */   private int deviceTypeInt;
/*     */   private int channelNumber;
/*     */   private String deviceId;
/*     */   private String deviceName;
/*     */   private List<DeviceModule> devModuleList;
/*     */   private List<ChannelInfo> channelList;
/*     */   
/*     */   public static int length(byte[] orgMsgBytes) {
/*  63 */     if (orgMsgBytes.length < 53) {
/*  64 */       return 0;
/*     */     }
/*  66 */     return 53 + 
/*  67 */       HexUtils.bytesToIntLittle(orgMsgBytes, 12);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public DevicePacket(byte[] orgMsgBytes) throws InvalidRFBMessageException {
/*  77 */     int deviceInfoLength = parseDeviceHeader(orgMsgBytes, 12, 41);
/*  78 */     parseDeviceBody(orgMsgBytes, 53, deviceInfoLength);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public DevicePacket(byte[] orgMsgBytes, int off, int length) throws InvalidRFBMessageException {
/*  90 */     parseDeviceBody(orgMsgBytes, off, length);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private int parseDeviceHeader(byte[] orgMsgBytes, int off, int length) {
/* 102 */     int deviceInfoLength = HexUtils.bytesToIntLittle(orgMsgBytes, off);
/* 103 */     this.deviceTypeInt = orgMsgBytes[off + 21];
/* 104 */     this.deviceType = String.valueOf(this.deviceTypeInt);
/* 105 */     return deviceInfoLength;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private void parseDeviceBody(byte[] orgMsgBytes, int off, int length) throws InvalidRFBMessageException {
/* 117 */     if (length % 133 != 0) {
/* 118 */       throw new InvalidRFBMessageException("Device information decoding error: Incorrect length");
/*     */     }
/* 120 */     int number = length / 133;
/* 121 */     this.devModuleList = new ArrayList<>();
/* 122 */     for (int index = 0; index < number; index++) {
/* 123 */       DeviceModule deviceModule = new DeviceModule();
/* 124 */       int start = off + 133 * index;
/* 125 */       deviceModule.setDeviceType(orgMsgBytes[start]);
/* 126 */       deviceModule.setDeviceTypeStr(String.valueOf(deviceModule.getDeviceType()));
/* 127 */       deviceModule.setDeviceId(HexUtils.bytesToAscii(orgMsgBytes, start + 11, 20));
/* 128 */       deviceModule.setDeviceName(HexUtils.bytesToAscii(orgMsgBytes, start + 31, 20));
/* 129 */       deviceModule.setHardwareVer(HexUtils.bytesToHexString(orgMsgBytes, start + 51, 5));
/* 130 */       deviceModule.setSoftwareVer(HexUtils.bytesToHexString(orgMsgBytes, start + 56, 5));
/* 131 */       deviceModule.setCascadeMode(orgMsgBytes[start + 61]);
/* 132 */       deviceModule.setSocketType(orgMsgBytes[start + 62]);
/* 133 */       deviceModule.setChannelNumber(orgMsgBytes[start + 63]);
/* 134 */       byte[] channelsStateBytes = new byte[64];
/* 135 */       System.arraycopy(orgMsgBytes, start + 64, channelsStateBytes, 0, 64);
/* 136 */       deviceModule.setChannelsState(channelsStateBytes);
/* 137 */       byte[] pathBytes = new byte[5];
/* 138 */       System.arraycopy(orgMsgBytes, start + 128, pathBytes, 0, 5);
/* 139 */       deviceModule.setPath(pathBytes);
/* 140 */       this.devModuleList.add(deviceModule);
/* 141 */       if (index == 0) {
/* 142 */         setDeviceId(deviceModule.getDeviceId());
/* 143 */         setDeviceName(deviceModule.getDeviceName());
/* 144 */         setChannelNumber(deviceModule.getChannelNumber());
/*     */       } 
/*     */     } 
/* 147 */     parseChannelInfo();
/*     */   }
/*     */   
/*     */   private void parseChannelInfo() {
/* 151 */     if (this.devModuleList.isEmpty()) {
/*     */       return;
/*     */     }
/* 154 */     byte[] channelsState = ((DeviceModule)this.devModuleList.get(0)).getChannelsState();
/* 155 */     this.channelList = new ArrayList<>();
/* 156 */     if (this.channelNumber <= channelsState.length) {
/* 157 */       for (int index = 0; index < this.channelNumber; index++) {
/* 158 */         ChannelInfo channelInfo = new ChannelInfo();
/* 159 */         channelInfo.setChannelNo(index);
/*     */         
/* 161 */         for (int i = 1; i < this.devModuleList.size(); i++) {
/* 162 */           byte[] path = ((DeviceModule)this.devModuleList.get(i)).getPath();
/* 163 */           if (path[1] == index) {
/* 164 */             channelInfo.setSocketType(((DeviceModule)this.devModuleList.get(i)).getSocketType());
/* 165 */             channelInfo.setDeviceId(((DeviceModule)this.devModuleList.get(i)).getDeviceId());
/* 166 */             channelInfo.setDeviceType(((DeviceModule)this.devModuleList.get(i)).getDeviceType());
/* 167 */             channelInfo.setDeviceName(((DeviceModule)this.devModuleList.get(i)).getDeviceName());
/* 168 */             channelInfo.setHardwareVer(((DeviceModule)this.devModuleList.get(i)).getHardwareVer());
/* 169 */             channelInfo.setSoftwareVer(((DeviceModule)this.devModuleList.get(i)).getSoftwareVer());
/*     */           } 
/*     */         } 
/* 172 */         if (channelsState[index] == 0) {
/* 173 */           channelInfo.setChannelState(0);
/*     */         } else {
/* 175 */           byte[] bitArray = HexUtils.getBooleanArray(channelsState[index]);
/* 176 */           if (bitArray[0] == 0) {
/* 177 */             channelInfo.setChannelState(1);
/*     */           } else {
/* 179 */             channelInfo.setChannelState(2);
/*     */           } 
/*     */         } 
/* 182 */         this.channelList.add(channelInfo);
/*     */       } 
/*     */     }
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public List<DeviceModule> getDevModuleList() {
/* 193 */     return this.devModuleList;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public String getDeviceType() {
/* 202 */     return this.deviceType;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setDeviceType(String deviceType) {
/* 211 */     this.deviceType = deviceType;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int getDeviceTypeInt() {
/* 220 */     return this.deviceTypeInt;
/*     */   }
/*     */   
/*     */   public void setDeviceTypeInt(int deviceTypeInt) {
/* 224 */     this.deviceTypeInt = deviceTypeInt;
/*     */   }
/*     */   
/*     */   public int getChannelNumber() {
/* 228 */     return this.channelNumber;
/*     */   }
/*     */   
/*     */   public void setChannelNumber(int channelNumber) {
/* 232 */     this.channelNumber = channelNumber;
/*     */   }
/*     */   
/*     */   public String getDeviceId() {
/* 236 */     return this.deviceId;
/*     */   }
/*     */   
/*     */   public void setDeviceId(String deviceId) {
/* 240 */     this.deviceId = deviceId;
/*     */   }
/*     */   
/*     */   public String getDeviceName() {
/* 244 */     return this.deviceName;
/*     */   }
/*     */   
/*     */   public void setDeviceName(String deviceName) {
/* 248 */     this.deviceName = deviceName;
/*     */   }
/*     */   
/*     */   public List<ChannelInfo> getChannelList() {
/* 252 */     return this.channelList;
/*     */   }
/*     */   
/*     */   public void setChannelList(List<ChannelInfo> channelList) {
/* 256 */     this.channelList = channelList;
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/baseinfo/DevicePacket.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */