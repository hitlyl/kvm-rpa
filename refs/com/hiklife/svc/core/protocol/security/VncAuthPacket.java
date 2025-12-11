/*    */ package com.hiklife.svc.core.protocol.security;
/*    */ import java.nio.ByteBuffer;
/*    */ import java.nio.charset.StandardCharsets;
/*    */ import org.slf4j.Logger;
/*    */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.core.protocol.InvalidRFBMessageException;
import refs.com.hiklife.svc.core.protocol.security.Auth;
import refs.com.hiklife.svc.core.protocol.security.SecurityInput;
import refs.com.hiklife.svc.core.protocol.security.VncAuthPacket;
import refs.com.hiklife.svc.util.DesCipher;
import refs.com.hiklife.svc.util.HexUtils;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class VncAuthPacket
/*    */   implements Auth
/*    */ {
/* 19 */   private static final Logger log = LoggerFactory.getLogger(VncAuthPacket.class);
/*    */ 
/*    */   
/*    */   private static final int CHALLENGE_LENGTH = 16;
/*    */ 
/*    */   
/*    */   private final byte[] challenge;
/*    */ 
/*    */   
/*    */   private final SecurityInput input;
/*    */ 
/*    */ 
/*    */   
/*    */   public VncAuthPacket(byte[] orgMsgBytes, SecurityInput input) throws InvalidRFBMessageException {
/* 33 */     if (orgMsgBytes.length == 16) {
/* 34 */       this.challenge = orgMsgBytes;
/*    */     } else {
/* 36 */       throw new InvalidRFBMessageException("VNC鉴权的随机数长度错误");
/*    */     } 
/* 38 */     this.input = input;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public byte[] encrypt() throws InvalidRFBMessageException {
/* 50 */     log.debug("CHALLENGE: {}", HexUtils.bytesToHexString(this.challenge));
/* 51 */     String password = this.input.getPassword();
/* 52 */     String user = this.input.getAccount();
/*    */     
/* 54 */     byte[] key = new byte[8];
/* 55 */     int pwdLen = password.length();
/*    */     
/* 57 */     byte[] utf8str = password.getBytes(StandardCharsets.UTF_8);
/* 58 */     for (int i = 0; i < 8; i++) {
/* 59 */       key[i] = (i < pwdLen) ? utf8str[i] : 0;
/*    */     }
/*    */     
/* 62 */     DesCipher des = new DesCipher(key);
/* 63 */     for (int j = 0; j < 16; j += 8) {
/* 64 */       des.encrypt(this.challenge, j, this.challenge, j);
/*    */     }
/*    */ 
/*    */     
/* 68 */     byte[] lengthBytes = HexUtils.intToBytesLittleEndian(16 + user.length() + 1);
/* 69 */     ByteBuffer binaryBuffer = ByteBuffer.allocate(16 + lengthBytes.length + user.length() + 1);
/* 70 */     binaryBuffer.put(lengthBytes);
/* 71 */     binaryBuffer.put(user.getBytes(StandardCharsets.US_ASCII));
/* 72 */     binaryBuffer.put((byte)-86);
/* 73 */     binaryBuffer.put(this.challenge);
/* 74 */     log.debug("VncAuth: {}", HexUtils.bytesToHexString(this.challenge));
/* 75 */     log.debug("VncAuth: {}", HexUtils.bytesToHexString(binaryBuffer.array()));
/* 76 */     return binaryBuffer.array();
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/security/VncAuthPacket.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */