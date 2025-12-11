/*    */ package com.cetiti.kvm.jni;
/*    */ 
/*    */ import java.io.IOException;
/*    */ import org.slf4j.Logger;
/*    */ import org.slf4j.LoggerFactory;

import refs.com.cetiti.kvm.jni.AudioDecoder;
import refs.com.cetiti.kvm.jni.G726State;
import refs.com.cetiti.kvm.jni.NativeLoader;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class AudioDecoder
/*    */ {
/* 17 */   private static final Logger log = LoggerFactory.getLogger(AudioDecoder.class);
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
/*    */   public static native byte[] decode(byte[] paramArrayOfbyte, G726State paramG726State1, G726State paramG726State2, CallBack paramCallBack);
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
/*    */   static {
/*    */     try {
/* 45 */       NativeLoader.loader("audio");
/* 46 */     } catch (IOException|ClassNotFoundException|java.net.URISyntaxException e) {
/* 47 */       log.error("Load audio lib error");
/*    */     } 
/*    */   }
/*    */   
/*    */   public static interface CallBack {
/*    */     void updateG726State(G726State param1G726State1, G726State param1G726State2);
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/cetiti/kvm/jni/AudioDecoder.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */