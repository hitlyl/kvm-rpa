/*     */ package com.hiklife.svc.core.protocol;
import refs.com.hiklife.svc.core.protocol.baseinfo.DevicePacket;
import refs.com.hiklife.svc.core.protocol.initialisation.ImageInfo;
import refs.com.hiklife.svc.core.protocol.normal.decoder.EncodingType;
import refs.com.hiklife.svc.core.protocol.security.SecurityType;
import refs.com.hiklife.svc.core.protocol.vm.MediaType;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ public class ProtocolContext
/*     */ {
/*     */   public static final int HANDLE_TYPE_VM = 1;
/*     */   public static final int HANDLE_TYPE_VIEWER = 0;
/*     */   private DevicePacket device;
/*     */   private String ip;
/*     */   private int port;
/*     */   private int channelNo;
/*     */   private SecurityType.Type securityType;
/*  22 */   private int handlerType = 0;
/*     */   
/*     */   private EncodingType encodingType;
/*     */   
/*     */   private long startTime;
/*     */   
/*     */   private boolean isTrueColor;
/*     */   
/*     */   private long frameFlow;
/*     */   
/*     */   private long flow;
/*     */   
/*     */   private ImageInfo imageInfo;
/*     */   
/*     */   private MediaType mediaType;
/*     */   
/*     */   private long readByteCount;
/*     */   
/*     */   private long writeByteCount;
/*     */   
/*     */   public DevicePacket getDevice() {
/*  43 */     return this.device;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setDevice(DevicePacket device) {
/*  52 */     this.device = device;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public String getIp() {
/*  61 */     return this.ip;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setIp(String ip) {
/*  70 */     this.ip = ip;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int getPort() {
/*  79 */     return this.port;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setPort(int port) {
/*  88 */     this.port = port;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int getChannelNo() {
/*  97 */     return this.channelNo;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setChannelNo(int channelNo) {
/* 106 */     this.channelNo = channelNo;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public SecurityType.Type getSecurityType() {
/* 115 */     return this.securityType;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setSecurityType(SecurityType.Type securityType) {
/* 124 */     this.securityType = securityType;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public EncodingType getEncodingType() {
/* 133 */     return this.encodingType;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setEncodingType(EncodingType encodingType) {
/* 142 */     this.encodingType = encodingType;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public long getStartTime() {
/* 151 */     return this.startTime;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setStartTime(long startTime) {
/* 160 */     this.startTime = startTime;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public boolean isTrueColor() {
/* 169 */     return this.isTrueColor;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setTrueColor(boolean trueColor) {
/* 178 */     this.isTrueColor = trueColor;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public long getFrameFlow() {
/* 187 */     return this.frameFlow;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setFrameFlow(long frameFlow) {
/* 196 */     this.frameFlow = frameFlow;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public long getFlow() {
/* 205 */     return this.flow;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setFlow(long flow) {
/* 214 */     this.flow = flow;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public ImageInfo getImageInfo() {
/* 223 */     return this.imageInfo;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setImageInfo(ImageInfo imageInfo) {
/* 232 */     this.imageInfo = imageInfo;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public MediaType getMediaType() {
/* 241 */     return this.mediaType;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setMediaType(MediaType mediaType) {
/* 250 */     this.mediaType = mediaType;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public long getReadByteCount() {
/* 259 */     return this.readByteCount;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setReadByteCount(long readByteCount) {
/* 268 */     this.readByteCount = readByteCount;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public long getWriteByteCount() {
/* 277 */     return this.writeByteCount;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setWriteByteCount(long writeByteCount) {
/* 286 */     this.writeByteCount = writeByteCount;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int getHandlerType() {
/* 295 */     return this.handlerType;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setHandlerType(int handlerType) {
/* 304 */     this.handlerType = handlerType;
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/ProtocolContext.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */