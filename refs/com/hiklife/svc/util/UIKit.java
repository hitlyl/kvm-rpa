/*    */ package com.hiklife.svc.util;
/*    */ 
/*    */ import java.awt.image.BufferedImage;
/*    */ import java.awt.image.DataBufferByte;
/*    */ import java.awt.image.WritableRaster;
/*    */ import org.bytedeco.ffmpeg.avutil.AVFrame;
/*    */ import org.bytedeco.javacpp.BytePointer;
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
/*    */ public class UIKit
/*    */ {
/*    */   public static BufferedImage getBufferedImage(AVFrame avFrame, BufferedImage bufferedImage) {
/* 25 */     if (bufferedImage == null) {
/*    */       
/* 27 */       bufferedImage = new BufferedImage(avFrame.width(), avFrame.height(), 5);
/* 28 */     } else if (bufferedImage.getWidth() != avFrame.width() || bufferedImage.getHeight() != avFrame.height()) {
/*    */       
/* 30 */       bufferedImage = new BufferedImage(avFrame.width(), avFrame.height(), 5);
/*    */     } 
/* 32 */     BytePointer bytePointer = avFrame.data(0).capacity(avFrame.height() * avFrame.linesize(0));
/* 33 */     WritableRaster raster = bufferedImage.getRaster();
/* 34 */     DataBufferByte dataBuffer = (DataBufferByte)raster.getDataBuffer();
/* 35 */     byte[] data = dataBuffer.getData();
/* 36 */     bytePointer.get(data);
/* 37 */     return bufferedImage;
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/util/UIKit.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */