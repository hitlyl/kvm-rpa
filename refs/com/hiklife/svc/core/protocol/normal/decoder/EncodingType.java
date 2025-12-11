/*    */ package com.hiklife.svc.core.protocol.normal.decoder;

import refs.com.hiklife.svc.core.protocol.normal.decoder.EncodingType;

/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public enum EncodingType
/*    */ {
/* 12 */   None(-1),
/*    */ 
/*    */ 
/*    */   
/* 16 */   H264(7),
/*    */ 
/*    */ 
/*    */   
/* 20 */   H265(9),
/*    */ 
/*    */ 
/*    */   
/* 24 */   IMAGE_INFO(-223);
/*    */   private final int code;
/*    */   
/*    */   EncodingType(int code) {
/* 28 */     this.code = code;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public static EncodingType parse(int code) {
/* 38 */     EncodingType[] values = values();
/* 39 */     for (EncodingType value : values) {
/* 40 */       if (value.getCode() == code) {
/* 41 */         return value;
/*    */       }
/*    */     } 
/* 44 */     return None;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public int getCode() {
/* 53 */     return this.code;
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/decoder/EncodingType.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */