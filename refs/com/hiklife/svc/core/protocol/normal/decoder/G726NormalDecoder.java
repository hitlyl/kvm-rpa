/*    */ package com.hiklife.svc.core.protocol.normal.decoder;
import refs.com.cetiti.kvm.jni.AudioDecoder;
import refs.com.cetiti.kvm.jni.G726State;
import refs.com.hiklife.svc.core.protocol.normal.decoder.G726Decoder;
import refs.com.hiklife.svc.core.protocol.normal.decoder.G726NormalDecoder;
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
/*    */ public class G726NormalDecoder
/*    */   extends G726Decoder
/*    */ {
/* 21 */   private G726State leftState = new G726State();
/* 22 */   private G726State rightState = new G726State();
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void decode(byte[] bytes, G726Decoder.Event event) {
/* 33 */     if (event != null) {
/* 34 */       byte[] des = AudioDecoder.decode(bytes, this.leftState, this.rightState, new AudioDecoder.CallBack()
/*    */           {
/*    */             public void updateG726State(G726State leftState, G726State rightState) {
/* 37 */               G726NormalDecoder.this.leftState = leftState;
/* 38 */               G726NormalDecoder.this.rightState = rightState;
/*    */             }
/*    */           });
/* 41 */       event.onAudioDecodeFrame(des);
/*    */     } 
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public G726State getLeftState() {
/* 51 */     return this.leftState;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void setLeftState(G726State leftState) {
/* 60 */     this.leftState = leftState;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public G726State getRightState() {
/* 69 */     return this.rightState;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void setRightState(G726State rightState) {
/* 78 */     this.rightState = rightState;
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/decoder/G726NormalDecoder.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */