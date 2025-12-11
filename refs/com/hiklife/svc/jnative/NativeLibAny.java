/*    */ package com.hiklife.svc.jnative;

import refs.com.hiklife.svc.jnative.NativeLib;
import refs.com.hiklife.svc.jnative.NativeMouseListener;

/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class NativeLibAny
/*    */   implements NativeLib
/*    */ {
/*    */   public int clipCursor(int left, int top, int right, int bottom, NativeMouseListener listener) {
/* 10 */     return 0;
/*    */   }
/*    */ 
/*    */ 
/*    */   
/*    */   public void releaseCursor() {}
/*    */ 
/*    */ 
/*    */   
/*    */   public boolean[] getLockKeyState() {
/* 20 */     return new boolean[] { false, false, false };
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/jnative/NativeLibAny.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */