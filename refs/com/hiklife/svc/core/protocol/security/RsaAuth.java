/*    */ package com.hiklife.svc.core.protocol.security;
/*    */ import org.slf4j.Logger;
/*    */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.core.protocol.InvalidRFBMessageException;
import refs.com.hiklife.svc.core.protocol.security.Auth;
import refs.com.hiklife.svc.core.protocol.security.RsaAuth;
import refs.com.hiklife.svc.core.protocol.security.SecurityInput;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class RsaAuth
/*    */   implements Auth
/*    */ {
/* 13 */   private static final Logger log = LoggerFactory.getLogger(RsaAuth.class);
/*    */ 
/*    */   
/*    */   private static final int CHALLENGE_LENGTH = 16;
/*    */ 
/*    */   
/*    */   private byte[] aesKey;
/*    */ 
/*    */   
/*    */   private SecurityInput input;
/*    */ 
/*    */   
/*    */   public RsaAuth(byte[] orgMsgBytes, SecurityInput input) throws InvalidRFBMessageException {
/* 26 */     if (orgMsgBytes.length == 16) {
/* 27 */       this.aesKey = orgMsgBytes;
/*    */     } else {
/* 29 */       throw new InvalidRFBMessageException("RSA鉴权的AESKey长度错误");
/*    */     } 
/* 31 */     this.input = input;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public byte[] encrypt() throws InvalidRFBMessageException {
/* 42 */     return new byte[0];
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/security/RsaAuth.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */