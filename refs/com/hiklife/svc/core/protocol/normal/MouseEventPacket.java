/*    */ package com.hiklife.svc.core.protocol.normal;
import refs.com.hiklife.svc.core.protocol.normal.WriteNormalType;
import refs.com.hiklife.svc.util.HexUtils;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class MouseEventPacket
/*    */ {
/*    */   private static final int LENGTH = 6;
/*    */   private final int mask;
/*    */   private int x;
/*    */   private int y;
/*    */   private final int type;
/*    */   
/*    */   public MouseEventPacket(int x, int y, int mask, int type) {
/* 17 */     this.x = x;
/* 18 */     this.y = y;
/* 19 */     this.mask = mask;
/* 20 */     this.type = type;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public byte[] buildRFB() {
/* 27 */     byte[] bytes = new byte[6];
/* 28 */     bytes[0] = WriteNormalType.PointerEvent.getCode();
/* 29 */     if (this.type == 0) {
/*    */       
/* 31 */       bytes[1] = (byte)(this.mask | 0x80);
/* 32 */       byte[] xBytes = HexUtils.signedShortToRegister((short)this.x);
/* 33 */       System.arraycopy(xBytes, 0, bytes, 2, 2);
/* 34 */       byte[] yBytes = HexUtils.signedShortToRegister((short)this.y);
/* 35 */       System.arraycopy(yBytes, 0, bytes, 4, 2);
/* 36 */       return bytes;
/* 37 */     }  if (this.type == 1) {
/* 38 */       bytes[1] = (byte)this.mask;
/*    */       
/* 40 */       if (this.x < 0) this.x = 0; 
/* 41 */       if (this.y < 0) this.y = 0; 
/* 42 */       byte[] xBytes = HexUtils.unsignedShortToRegister((short)this.x);
/* 43 */       System.arraycopy(xBytes, 0, bytes, 2, 2);
/* 44 */       byte[] yBytes = HexUtils.unsignedShortToRegister((short)this.y);
/* 45 */       System.arraycopy(yBytes, 0, bytes, 4, 2);
/* 46 */       return bytes;
/*    */     } 
/* 48 */     return bytes;
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/MouseEventPacket.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */