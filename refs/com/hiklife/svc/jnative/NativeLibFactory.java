/*    */ package com.hiklife.svc.jnative;
/*    */ import org.slf4j.Logger;
/*    */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.jnative.NativeLib;
import refs.com.hiklife.svc.jnative.NativeLibAny;
import refs.com.hiklife.svc.jnative.NativeLibFactory;
import refs.com.hiklife.svc.jnative.linux.NativeLibLinux;
import refs.com.hiklife.svc.jnative.win.NativeLibWin;
import refs.com.hiklife.svc.util.OSUtils;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class NativeLibFactory
/*    */ {
/* 14 */   private static final Logger log = LoggerFactory.getLogger(NativeLibFactory.class);
/* 15 */   private static volatile NativeLib jnaLib = null;
/*    */   public static synchronized NativeLib createJnaLib() {
/* 17 */     if (jnaLib == null) {
/* 18 */       if (OSUtils.isWin()) {
/* 19 */         jnaLib = (NativeLib)new NativeLibWin();
/* 20 */       } else if (OSUtils.isLinux()) {
/* 21 */         jnaLib = (NativeLib)new NativeLibLinux();
/*    */       } else {
/* 23 */         jnaLib = new NativeLibAny();
/* 24 */         log.error("Unsupported operating system");
/*    */       } 
/*    */     }
/* 27 */     return jnaLib;
/*    */   }
/*    */ 
/*    */   
/*    */   public static void main(String[] args) throws Exception {
/* 32 */     NativeLib clipper = createJnaLib();
/*    */     
/* 34 */     clipper.clipCursor(300, 300, 600, 600, null);
/*    */     
/* 36 */     long delay = 0L;
/* 37 */     while (delay < 10000L) {
/*    */       try {
/* 39 */         Thread.sleep(1000L);
/* 40 */         delay += 1000L;
/* 41 */       } catch (InterruptedException ex) {
/*    */         break;
/*    */       } 
/*    */     } 
/*    */ 
/*    */     
/* 47 */     clipper.releaseCursor();
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/jnative/NativeLibFactory.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */