/*    */ package com.hiklife.svc.jnative.linux;
/*    */ import org.slf4j.Logger;
/*    */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.jnative.NativeLib;
import refs.com.hiklife.svc.jnative.NativeMouseListener;
import refs.com.hiklife.svc.jnative.linux.NativeLibLinux;
import refs.com.hiklife.svc.jnative.linux.RawInputLinux;
import refs.com.sun.jna.NativeLong;
import refs.com.sun.jna.platform.unix.X11;
/*    */ 
/*    */ 
/*    */ 
/*    */ public class NativeLibLinux
/*    */   implements NativeLib
/*    */ {
/* 15 */   private static final Logger log = LoggerFactory.getLogger(NativeLibLinux.class);
/*    */   
/*    */   private static final int LedCapsLockMask = 1;
/*    */   
/*    */   private static final int LedNumLockMask = 2;
/*    */   private static final int LedScrollLockMask = 4;
/*    */   
/*    */   public int clipCursor(int _left, int _top, int _right, int _bottom, NativeMouseListener listener) {
/* 23 */     RawInputLinux.instance().setListener(listener);
/* 24 */     return RawInputLinux.instance().openInput();
/*    */   }
/*    */ 
/*    */   
/*    */   public void releaseCursor() {
/* 29 */     RawInputLinux.instance().release();
/*    */   }
/*    */ 
/*    */ 
/*    */   
/*    */   public boolean[] getLockKeyState() {
/* 35 */     X11.Display display = X11.INSTANCE.XOpenDisplay(null);
/* 36 */     boolean[] result = new boolean[3];
/* 37 */     if (display == null) {
/* 38 */       log.error("无法打开 X11 显示");
/* 39 */       return result;
/*    */     } 
/*    */     try {
/* 42 */       X11.XKeyboardStateRef state = new X11.XKeyboardStateRef();
/* 43 */       X11.INSTANCE.XGetKeyboardControl(display, state);
/* 44 */       NativeLong ledMask = state.led_mask;
/* 45 */       result[0] = ((ledMask.byteValue() & 0x1) != 0);
/* 46 */       result[1] = ((ledMask.byteValue() & 0x2) != 0);
/* 47 */       result[2] = ((ledMask.byteValue() & 0x4) != 0);
/* 48 */       return result;
/*    */     } finally {
/* 50 */       X11.INSTANCE.XCloseDisplay(display);
/*    */     } 
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/jnative/linux/NativeLibLinux.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */