/*    */ package com.hiklife.svc.core.protocol.normal;

import refs.com.hiklife.svc.core.protocol.normal.ReadNormalType;

/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public enum ReadNormalType
/*    */ {
/* 12 */   None((byte)-1),
/*    */ 
/*    */ 
/*    */ 
/*    */   
/* 17 */   FrameBufferUpdate((byte)0),
/*    */ 
/*    */ 
/*    */   
/* 21 */   SetColourMapEntries((byte)1),
/*    */ 
/*    */ 
/*    */   
/* 25 */   Bell((byte)2),
/*    */ 
/*    */ 
/*    */   
/* 29 */   ServerCutText((byte)3),
/*    */ 
/*    */ 
/*    */   
/* 33 */   AudioBufferUpdate((byte)4),
/*    */ 
/*    */ 
/*    */   
/* 37 */   VMRead((byte)10),
/*    */ 
/*    */ 
/*    */   
/* 41 */   VMWrite((byte)11),
/*    */ 
/*    */ 
/*    */ 
/*    */   
/* 46 */   VideoParam((byte)102),
/*    */ 
/*    */ 
/*    */   
/* 50 */   KeyStatus((byte)103),
/*    */ 
/*    */ 
/*    */   
/* 54 */   DeviceInfo((byte)104),
/*    */ 
/*    */ 
/*    */   
/* 58 */   AudioParam((byte)105),
/*    */ 
/*    */ 
/*    */   
/* 62 */   MouseType((byte)106),
/*    */ 
/*    */ 
/*    */   
/* 66 */   VideoLevel((byte)107),
/*    */ 
/*    */ 
/*    */   
/* 70 */   BroadcastStatus((byte)-55),
/*    */ 
/*    */ 
/*    */   
/* 74 */   BroadcastSetStatus((byte)-54);
/*    */   
/*    */   private final byte code;
/*    */   
/*    */   ReadNormalType(byte code) {
/* 79 */     this.code = code;
/*    */   }
/*    */   
/*    */   public static ReadNormalType parse(byte code) {
/* 83 */     ReadNormalType[] values = values();
/* 84 */     for (ReadNormalType value : values) {
/* 85 */       if (value.getCode() == code) {
/* 86 */         return value;
/*    */       }
/*    */     } 
/* 89 */     return None;
/*    */   }
/*    */   
/*    */   public byte getCode() {
/* 93 */     return this.code;
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/ReadNormalType.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */