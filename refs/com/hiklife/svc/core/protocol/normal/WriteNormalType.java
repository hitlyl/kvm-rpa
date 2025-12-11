/*     */ package com.hiklife.svc.core.protocol.normal;

import refs.com.hiklife.svc.core.protocol.normal.WriteNormalType;

/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ public enum WriteNormalType
/*     */ {
/*  12 */   None((byte)-1),
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*  17 */   SetPixelFormat((byte)0),
/*     */ 
/*     */ 
/*     */   
/*  21 */   FixColourMapEntries((byte)1),
/*     */ 
/*     */ 
/*     */   
/*  25 */   SetEncodings((byte)2),
/*     */ 
/*     */ 
/*     */   
/*  29 */   FramebufferUpdateRequest((byte)3),
/*     */ 
/*     */ 
/*     */   
/*  33 */   KeyEvent((byte)4),
/*     */ 
/*     */ 
/*     */   
/*  37 */   PointerEvent((byte)5),
/*     */ 
/*     */ 
/*     */   
/*  41 */   ClientCutText((byte)6),
/*     */ 
/*     */ 
/*     */   
/*  45 */   AudioRequest((byte)7),
/*     */ 
/*     */ 
/*     */   
/*  49 */   VMLink((byte)10),
/*     */ 
/*     */ 
/*     */   
/*  53 */   VMClose((byte)11),
/*     */ 
/*     */ 
/*     */   
/*  57 */   VMData((byte)12),
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*  62 */   ClientHere((byte)101),
/*     */ 
/*     */ 
/*     */   
/*  66 */   VideoParamRequest((byte)102),
/*     */ 
/*     */ 
/*     */   
/*  70 */   SetCustomVideoParam((byte)103),
/*     */ 
/*     */ 
/*     */   
/*  74 */   KeyStatusRequest((byte)104),
/*     */ 
/*     */ 
/*     */   
/*  78 */   DeviceInfoRequest((byte)105),
/*     */ 
/*     */ 
/*     */   
/*  82 */   PortSwitch((byte)106),
/*     */ 
/*     */ 
/*     */   
/*  86 */   AudioParamRequest((byte)107),
/*     */ 
/*     */ 
/*     */   
/*  90 */   SetCustomAudioParam((byte)108),
/*     */ 
/*     */ 
/*     */   
/*  94 */   MouseTypeRequest((byte)109),
/*     */ 
/*     */ 
/*     */   
/*  98 */   SetMouseType((byte)110),
/*     */ 
/*     */ 
/*     */   
/* 102 */   VideolevelRequest((byte)111),
/*     */ 
/*     */ 
/*     */   
/* 106 */   SetVideolevel((byte)112);
/*     */   
/*     */   private byte code;
/*     */ 
/*     */   
/*     */   WriteNormalType(byte code) {
/* 112 */     this.code = code;
/*     */   }
/*     */   
/*     */   public static WriteNormalType parse(byte code) {
/* 116 */     WriteNormalType[] values = values();
/* 117 */     for (WriteNormalType value : values) {
/* 118 */       if (code == value.getCode()) {
/* 119 */         return value;
/*     */       }
/*     */     } 
/* 122 */     return None;
/*     */   }
/*     */   
/*     */   public byte getCode() {
/* 126 */     return this.code;
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/WriteNormalType.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */