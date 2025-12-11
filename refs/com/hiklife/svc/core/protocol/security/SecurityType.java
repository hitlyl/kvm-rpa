/*    */ package com.hiklife.svc.core.protocol.security;
/*    */ import java.util.ArrayList;
/*    */ import java.util.List;

import refs.com.hiklife.svc.core.protocol.InvalidRFBMessageException;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class SecurityType
/*    */ {
/* 14 */   private List<Type> types = new ArrayList<>();
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public SecurityType(byte[] orgMsgBytes) throws InvalidRFBMessageException {
/* 23 */     int securityTypeNumber = orgMsgBytes[0];
/* 24 */     if (securityTypeNumber != 0) {
/* 25 */       for (int index = 1; index < orgMsgBytes.length; index++) {
/* 26 */         Type type = Type.parse(orgMsgBytes[index]);
/* 27 */         this.types.add(type);
/*    */       } 
/*    */     } else {
/* 30 */       throw new InvalidRFBMessageException("没有得到设备的鉴权方式");
/*    */     } 
/*    */   }
/*    */   public static int length(byte[] orgMsgBytes, int offSize) {
/* 34 */     int securityTypeNumber = orgMsgBytes[offSize];
/* 35 */     return 1 + securityTypeNumber;
/*    */   }
/*    */   
/*    */   public static int length(byte[] orgMsgBytes) {
/* 39 */     return length(orgMsgBytes, 0);
/*    */   }
/*    */ 
/*    */   
/*    */   public List<Type> getTypes() {
/* 44 */     return this.types;
/*    */   }
/*    */   
/*    */   public void setTypes(List<Type> types) {
/* 48 */     this.types = types;
/*    */   }
/*    */ 
/*    */ 
/*    */   
/*    */   public enum Type
/*    */   {
/* 55 */     INVALID((byte)0),
/* 56 */     NONE((byte)1),
/* 57 */     VNC_AUTH((byte)2),
/* 58 */     RSA((byte)9),
/* 59 */     REMOTE_AUTH((byte)10),
/* 60 */     CENTRALIZE_AUTH((byte)20),
/* 61 */     U_KEY((byte)8);
/*    */     
/*    */     private byte code;
/*    */     
/*    */     Type(byte code) {
/* 66 */       this.code = code;
/*    */     }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */     
/*    */     public static Type parse(byte code) {
/* 76 */       Type[] values = values();
/* 77 */       for (Type value : values) {
/* 78 */         if (value.getCode() == code) {
/* 79 */           return value;
/*    */         }
/*    */       } 
/* 82 */       return INVALID;
/*    */     }
/*    */     
/*    */     public byte getCode() {
/* 86 */       return this.code;
/*    */     }
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/security/SecurityType.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */