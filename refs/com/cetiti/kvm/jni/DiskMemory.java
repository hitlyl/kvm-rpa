/*    */ package com.cetiti.kvm.jni;
/*    */ 
/*    */ import java.io.IOException;
/*    */ import org.slf4j.Logger;
/*    */ import org.slf4j.LoggerFactory;

import refs.com.cetiti.kvm.jni.DiskMemory;
import refs.com.cetiti.kvm.jni.NativeLoader;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class DiskMemory
/*    */ {
/* 16 */   private static final Logger log = LoggerFactory.getLogger(DiskMemory.class);
/*    */   
/*    */   static {
/*    */     try {
/* 20 */       NativeLoader.loader("diskmemory");
/* 21 */     } catch (IOException|ClassNotFoundException|java.net.URISyntaxException e) {
/* 22 */       log.error("Load diskmemory lib error");
/*    */     } 
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
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   private int sectorCount;
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
/*    */   private int bytePerSector;
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
/*    */   public int getAllSectorCount() {
/* 71 */     return this.sectorCount;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void setSectorCount(int sectorCount) {
/* 80 */     this.sectorCount = sectorCount;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public int getBytePerSector() {
/* 89 */     return this.bytePerSector;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void setBytePerSector(int bytePerSector) {
/* 98 */     this.bytePerSector = bytePerSector;
/*    */   }
/*    */   
/*    */   public static native DiskMemory getDiskMemory(String paramString);
/*    */   
/*    */   public static native byte[] getMemoryByte(String paramString, int paramInt1, int paramInt2);
/*    */   
/*    */   public static native int writeMemoryBytes(String paramString, byte[] paramArrayOfbyte, int paramInt1, int paramInt2);
/*    */   
/*    */   public static native boolean closeHandle(String paramString);
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/cetiti/kvm/jni/DiskMemory.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */