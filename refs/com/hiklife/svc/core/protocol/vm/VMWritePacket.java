/*    */ package com.hiklife.svc.core.protocol.vm;
/*    */ import org.slf4j.Logger;
/*    */ import org.slf4j.LoggerFactory;

import refs.com.cetiti.kvm.jni.DiskMemory;
import refs.com.hiklife.svc.core.protocol.vm.MediaType;
import refs.com.hiklife.svc.core.protocol.vm.VMWritePacket;
import refs.com.hiklife.svc.util.HexUtils;
/*    */ 
/*    */ public class VMWritePacket
/*    */ {
/* 10 */   private static final Logger log = LoggerFactory.getLogger(VMWritePacket.class);
/*    */   
/*    */   public static final int LENGTH = 15;
/*    */   
/*    */   private int count;
/*    */   
/*    */   public VMWritePacket(byte[] orgMsgBytes, MediaType mediaType) {
/* 17 */     byte[] countByte = { 0, 0, orgMsgBytes[13], orgMsgBytes[14] };
/* 18 */     this.count = HexUtils.bytesToIntBigEndian(countByte, 0);
/* 19 */     byte[] dataByte = new byte[this.count];
/* 20 */     byte[] offsetByte = { orgMsgBytes[9], orgMsgBytes[10], orgMsgBytes[11], orgMsgBytes[12] };
/* 21 */     int offset = HexUtils.bytesToIntBigEndian(offsetByte, 0);
/*    */     
/* 23 */     System.arraycopy(orgMsgBytes, 15, dataByte, 0, dataByte.length);
/* 24 */     DiskMemory.writeMemoryBytes(mediaType.getDriverPath(), dataByte, offset, this.count);
/*    */     
/* 26 */     log.debug("偏移{},总数{}", Integer.valueOf(offset), Integer.valueOf(this.count));
/* 27 */     log.debug("服务器写入: {}", HexUtils.bytesToHexString(dataByte));
/*    */   }
/*    */   
/*    */   public int getCount() {
/* 31 */     return this.count;
/*    */   }
/*    */   
/*    */   public void setCount(int count) {
/* 35 */     this.count = count;
/*    */   }
/*    */   
/*    */   public static int length(byte[] orgMsgBytes) {
/* 39 */     byte[] lengthByte = new byte[4];
/* 40 */     lengthByte[2] = orgMsgBytes[13];
/* 41 */     lengthByte[3] = orgMsgBytes[14];
/*    */     
/* 43 */     int audioSize = HexUtils.registersToInt(lengthByte);
/* 44 */     return audioSize + 15;
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/vm/VMWritePacket.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */