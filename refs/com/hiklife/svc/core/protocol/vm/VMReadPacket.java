/*    */ package com.hiklife.svc.core.protocol.vm;
/*    */ import org.slf4j.Logger;
/*    */ import org.slf4j.LoggerFactory;

import refs.com.cetiti.kvm.jni.DiskMemory;
import refs.com.hiklife.svc.core.protocol.vm.MediaType;
import refs.com.hiklife.svc.core.protocol.vm.VMReadPacket;
import refs.com.hiklife.svc.util.HexUtils;
/*    */ 
/*    */ public class VMReadPacket
/*    */ {
/* 10 */   private static final Logger log = LoggerFactory.getLogger(VMReadPacket.class);
/*    */   
/* 12 */   private static final byte[] SEND_VM_DATA = new byte[] { 12, 0, 0, 0 };
/*    */   private int offset;
/*    */   private int count;
/*    */   private final MediaType mediaType;
/*    */   
/*    */   public VMReadPacket(byte[] orgMsgBytes, MediaType mediaType) {
/* 18 */     this.mediaType = mediaType;
/* 19 */     int msgLength = orgMsgBytes.length;
/* 20 */     byte[] countByte = { 0, 0, orgMsgBytes[msgLength - 2], orgMsgBytes[msgLength - 1] };
/* 21 */     this.count = HexUtils.bytesToIntBigEndian(countByte, 0);
/* 22 */     if (this.count == 0) {
/* 23 */       this.count = 65536;
/*    */     }
/*    */     
/* 26 */     byte[] offsetByte = { orgMsgBytes[9], orgMsgBytes[10], orgMsgBytes[11], orgMsgBytes[12] };
/* 27 */     this.offset = HexUtils.bytesToIntBigEndian(offsetByte, 0);
/* 28 */     log.debug("readVM: {}", HexUtils.bytesToHexString(orgMsgBytes));
/* 29 */     log.debug("offset: {}, count: {}", Integer.valueOf(this.offset), Integer.valueOf(this.count));
/*    */   }
/*    */   
/*    */   public int getOffset() {
/* 33 */     return this.offset;
/*    */   }
/*    */   
/*    */   public void setOffset(int offset) {
/* 37 */     this.offset = offset;
/*    */   }
/*    */   
/*    */   public int getCount() {
/* 41 */     return this.count;
/*    */   }
/*    */   
/*    */   public void setCount(int count) {
/* 45 */     this.count = count;
/*    */   }
/*    */   
/*    */   public byte[] buildRFB() {
/* 49 */     byte[] bytes = new byte[6 + this.count];
/* 50 */     System.arraycopy(SEND_VM_DATA, 0, bytes, 0, 4);
/* 51 */     System.arraycopy(HexUtils.intToBytesBigEndian(this.count), 2, bytes, 4, 2);
/* 52 */     byte[] data = DiskMemory.getMemoryByte(this.mediaType.getDriverPath(), this.offset, this.count);
/* 53 */     System.arraycopy(data, 0, bytes, 6, data.length);
/* 54 */     return bytes;
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/vm/VMReadPacket.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */