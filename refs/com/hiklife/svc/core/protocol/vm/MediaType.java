/*    */ package com.hiklife.svc.core.protocol.vm;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class MediaType
/*    */ {
/*    */   private String path;
/*    */   private Type type;
/*    */   private boolean isWriteAndRead;
/*    */   
/*    */   public MediaType(String path, Type type) {
/* 13 */     this.path = path;
/* 14 */     this.type = type;
/*    */   }
/*    */   
/*    */   public String getDriverPath() {
/* 18 */     if (this.path.endsWith(":\\")) {
/* 19 */       return "\\\\.\\" + this.path.substring(0, 2);
/*    */     }
/* 21 */     return this.path;
/*    */   }
/*    */   
/*    */   public enum Type
/*    */   {
/* 26 */     ISO, UDISK, CDROM;
/*    */   }
/*    */   
/*    */   public String getPath() {
/* 30 */     return this.path;
/*    */   }
/*    */   
/*    */   public void setPath(String path) {
/* 34 */     this.path = path;
/*    */   }
/*    */   
/*    */   public Type getType() {
/* 38 */     return this.type;
/*    */   }
/*    */   
/*    */   public void setType(Type type) {
/* 42 */     this.type = type;
/*    */   }
/*    */   
/*    */   public boolean isWriteAndRead() {
/* 46 */     return this.isWriteAndRead;
/*    */   }
/*    */   
/*    */   public void setWriteAndRead(boolean writeAndRead) {
/* 50 */     this.isWriteAndRead = writeAndRead;
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/vm/MediaType.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */