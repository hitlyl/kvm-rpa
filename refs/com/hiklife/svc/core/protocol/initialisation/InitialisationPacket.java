/*    */ package com.hiklife.svc.core.protocol.initialisation;
import refs.com.hiklife.svc.core.protocol.initialisation.ImageInfo;
import refs.com.hiklife.svc.util.HexUtils;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class InitialisationPacket
/*    */ {
/*    */   private ImageInfo imageInfo;
/*    */   private String deviceName;
/*    */   
/*    */   public InitialisationPacket(ImageInfo imageInfo, String deviceName) {
/* 29 */     this.imageInfo = imageInfo;
/* 30 */     this.deviceName = deviceName;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public InitialisationPacket(byte[] orgMsgBytes) {
/* 39 */     this.imageInfo = new ImageInfo();
/* 40 */     this.imageInfo.setWidth(HexUtils.registerToUnsignedShort(orgMsgBytes));
/* 41 */     this.imageInfo.setHeight(HexUtils.registerToUnsignedShort(orgMsgBytes, 2));
/* 42 */     int devNameLength = HexUtils.bytesToIntBigEndian(orgMsgBytes, 20);
/* 43 */     this.deviceName = HexUtils.bytesToAscii(orgMsgBytes, 24, devNameLength);
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public String getDeviceName() {
/* 52 */     return this.deviceName;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void setDeviceName(String deviceName) {
/* 61 */     this.deviceName = deviceName;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public ImageInfo getImageInfo() {
/* 70 */     return this.imageInfo;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void setImageInfo(ImageInfo imageInfo) {
/* 79 */     this.imageInfo = imageInfo;
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/initialisation/InitialisationPacket.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */