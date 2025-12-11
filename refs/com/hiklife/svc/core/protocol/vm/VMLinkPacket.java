/*    */ package com.hiklife.svc.core.protocol.vm;
/*    */ import org.slf4j.Logger;
/*    */ import org.slf4j.LoggerFactory;

import refs.com.cetiti.kvm.jni.DiskMemory;
import refs.com.hiklife.svc.core.protocol.InvalidRFBMessageException;
import refs.com.hiklife.svc.core.protocol.vm.DiskFactory;
import refs.com.hiklife.svc.core.protocol.vm.MediaType;
import refs.com.hiklife.svc.core.protocol.vm.VMLinkPacket;
import refs.com.hiklife.svc.util.HexUtils;
/*    */ 
/*    */ public class VMLinkPacket
/*    */ {
/* 11 */   private static final Logger log = LoggerFactory.getLogger(VMLinkPacket.class);
/* 12 */   private static final byte[] TYPE_VM_LINK = new byte[] { 10, 0, 0, 0 };
/*    */   private final MediaType mediaType;
/*    */   
/*    */   public VMLinkPacket(MediaType mediaType) {
/* 16 */     this.mediaType = mediaType;
/*    */   }
/*    */   public byte[] buildRFB() throws InvalidRFBMessageException {
/* 19 */     byte[] bytes = new byte[16];
/* 20 */     System.arraycopy(TYPE_VM_LINK, 0, bytes, 0, 4);
/*    */     
/* 22 */     bytes[4] = 0;
/* 23 */     if (this.mediaType.getType() == MediaType.Type.ISO || this.mediaType.getType() == MediaType.Type.CDROM) {
/* 24 */       bytes[4] = 1;
/*    */     }
/* 26 */     bytes[5] = 1;
/* 27 */     if (this.mediaType.isWriteAndRead()) {
/* 28 */       bytes[5] = 0;
/*    */     }
/* 30 */     bytes[6] = 0;
/* 31 */     bytes[7] = 0;
/* 32 */     DiskMemory diskMemory = DiskFactory.getDiskMemory(this.mediaType.getDriverPath());
/* 33 */     int sectorByteCount = diskMemory.getBytePerSector();
/* 34 */     byte[] sectorBytes = HexUtils.intToBytesBigEndian(sectorByteCount);
/* 35 */     System.arraycopy(sectorBytes, 0, bytes, 8, 4);
/* 36 */     int sectorCount = diskMemory.getAllSectorCount();
/* 37 */     log.debug("扇区数量{}", Integer.valueOf(sectorCount));
/* 38 */     if (sectorCount <= 0) {
/* 39 */       throw new InvalidRFBMessageException("打开磁盘失败");
/*    */     }
/* 41 */     byte[] sectors = HexUtils.intToBytesBigEndian(sectorCount);
/* 42 */     System.arraycopy(sectors, 0, bytes, 12, 4);
/* 43 */     return bytes;
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/vm/VMLinkPacket.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */