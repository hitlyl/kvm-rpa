/*    */ package com.hiklife.svc.jnative.win;
/*    */ import org.slf4j.Logger;
/*    */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.jnative.NativeLib;
import refs.com.hiklife.svc.jnative.NativeMouseListener;
import refs.com.hiklife.svc.jnative.win.NativeLibWin;
import refs.com.hiklife.svc.jnative.win.RawInputWin;
import refs.com.hiklife.svc.jnative.win.User32Ext;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class NativeLibWin
/*    */   implements NativeLib
/*    */ {
/* 15 */   private static final Logger log = LoggerFactory.getLogger(NativeLibWin.class);
/*    */   private boolean isClipped = false;
/*    */   
/*    */   public int clipCursor(int left, int top, int right, int bottom, NativeMouseListener listener) {
/* 19 */     if (!this.isClipped) {
/* 20 */       User32Ext.RECT.ByReference rectRef = new User32Ext.RECT.ByReference();
/* 21 */       rectRef.left = left;
/* 22 */       rectRef.top = top;
/* 23 */       rectRef.right = right;
/* 24 */       rectRef.bottom = bottom;
/*    */       
/* 26 */       boolean success = User32Ext.INSTANCE.ClipCursor(rectRef);
/* 27 */       if (success) {
/* 28 */         this.isClipped = true;
/* 29 */         log.info("Successfully restricted cursor.");
/*    */       } else {
/* 31 */         log.error("Failed to restrict cursor.");
/*    */       } 
/* 33 */       RawInputWin.instance().setListener(listener);
/* 34 */       RawInputWin.instance().openInput();
/*    */     } 
/* 36 */     return 0;
/*    */   }
/*    */ 
/*    */   
/*    */   public void releaseCursor() {
/* 41 */     if (this.isClipped) {
/* 42 */       User32Ext.INSTANCE.ClipCursor(null);
/* 43 */       this.isClipped = false;
/* 44 */       RawInputWin.instance().releaseWindow();
/* 45 */       log.info("Successfully release cursor.");
/*    */     } else {
/* 47 */       log.info("Cursor is not clipped.");
/*    */     } 
/*    */   }
/*    */ 
/*    */ 
/*    */   
/*    */   public boolean[] getLockKeyState() {
/* 54 */     boolean[] result = new boolean[3];
/* 55 */     result[0] = (User32Ext.INSTANCE.GetKeyState(20) == 1);
/* 56 */     result[1] = (User32Ext.INSTANCE.GetKeyState(144) == 1);
/* 57 */     result[2] = (User32Ext.INSTANCE.GetKeyState(145) == 1);
/* 58 */     return result;
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/jnative/win/NativeLibWin.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */