/*    */ package com.hiklife.svc.jnative.linux;
import refs.com.hiklife.svc.jnative.linux.LibCExt;
import refs.com.sun.jna.Library;
import refs.com.sun.jna.Native;
import refs.com.sun.jna.Pointer;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public interface LibCExt
/*    */   extends Library
/*    */ {
/*    */   public static final int EVIOCGRAB = 1074021776;
/*    */   public static final int EVIOCGRAB_ENABLE = 1;
/*    */   public static final int EVIOCGRAB_DISABLE = 0;
/*    */   public static final int O_RDONLY = 0;
/* 17 */   public static final LibCExt INSTANCE = (LibCExt)Native.load("c", LibCExt.class);
/*    */   
/*    */   int open(String paramString, int paramInt);
/*    */   
/*    */   int read(int paramInt1, Pointer paramPointer, int paramInt2);
/*    */   
/*    */   int close(int paramInt);
/*    */   
/*    */   int ioctl(int paramInt, long paramLong, Object... paramVarArgs);
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/jnative/linux/LibCExt.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */