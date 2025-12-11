/*     */ package com.hiklife.svc.viewer;
/*     */ import java.io.File;
/*     */ import java.io.FileInputStream;
/*     */ import java.io.IOException;
/*     */ import javax.sound.sampled.AudioFormat;
/*     */ import javax.sound.sampled.AudioSystem;
/*     */ import javax.sound.sampled.DataLine;
/*     */ import javax.sound.sampled.LineUnavailableException;
/*     */ import javax.sound.sampled.SourceDataLine;
/*     */ import org.slf4j.Logger;
/*     */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.core.protocol.normal.decoder.G726Decoder;
import refs.com.hiklife.svc.core.protocol.normal.decoder.G726NormalDecoder;
import refs.com.hiklife.svc.viewer.AudioPlayThreadPool;
import refs.com.hiklife.svc.viewer.AudioPlayTrack;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ public class AudioPlayTrack
/*     */ {
/*  21 */   private static final Logger log = LoggerFactory.getLogger(AudioPlayTrack.class);
/*     */   
/*     */   private static final int SAMPLE_RATE = 8000;
/*     */   
/*     */   private static final int SAMPLE_SIZE_IN_BITS = 16;
/*     */   
/*     */   private static final int CHANNELS = 2;
/*     */   
/*     */   private static final int FRAME_SIZE = 4;
/*     */   
/*     */   private static final int FRAME_RATE = 8000;
/*     */   
/*     */   private static final int CHANNELS_HISILICON = 1;
/*     */   
/*     */   private static final int FRAME_SIZE_HISILICON = 2;
/*     */   
/*     */   private SourceDataLine sourceDataLine;
/*     */   
/*     */   public AudioPlayTrack(boolean isHiSilicon) {
/*     */     AudioFormat audioFormat;
/*  41 */     if (isHiSilicon) {
/*  42 */       audioFormat = new AudioFormat(AudioFormat.Encoding.PCM_SIGNED, 8000.0F, 16, 1, 2, 8000.0F, false);
/*     */ 
/*     */ 
/*     */     
/*     */     }
/*     */     else {
/*     */ 
/*     */ 
/*     */       
/*  51 */       audioFormat = new AudioFormat(AudioFormat.Encoding.PCM_SIGNED, 8000.0F, 16, 2, 4, 8000.0F, false);
/*     */     } 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */     
/*  61 */     DataLine.Info dataLineInfo = new DataLine.Info(SourceDataLine.class, audioFormat, -1);
/*     */     
/*     */     try {
/*  64 */       this.sourceDataLine = (SourceDataLine)AudioSystem.getLine(dataLineInfo);
/*  65 */       this.sourceDataLine.open(audioFormat);
/*  66 */       this.sourceDataLine.start();
/*  67 */     } catch (LineUnavailableException e) {
/*  68 */       log.error(e.toString());
/*     */     } 
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public AudioPlayTrack() {
/*  76 */     this(false);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void destroy() {
/*  83 */     if (this.sourceDataLine != null) {
/*  84 */       this.sourceDataLine.close();
/*     */     }
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void play(byte[] bytes) {
/*  93 */     AudioPlayThreadPool.getInstance().execute(new HandlePlay(bytes));
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   class HandlePlay
/*     */     implements Runnable
/*     */   {
/*     */     private final byte[] bytes;
/*     */ 
/*     */ 
/*     */     
/*     */     HandlePlay(byte[] bytes) {
/* 107 */       this.bytes = bytes;
/*     */     }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */     
/*     */     public void run() {
/* 115 */       if (AudioPlayTrack.this.sourceDataLine != null && AudioPlayTrack.this.sourceDataLine.isOpen()) {
/* 116 */         AudioPlayTrack.this.sourceDataLine.write(this.bytes, 0, this.bytes.length);
/*     */       }
/*     */     }
/*     */   }
/*     */   
/*     */   public static void main(String[] args) throws IOException {
/* 122 */     int FRAME_SIZE = 40;
/*     */     
/* 124 */     final AudioPlayTrack audioPlayTrack = new AudioPlayTrack(true);
/* 125 */     File file = new File("D:\\Code\\iv3\\iv3-svc\\doc\\audio.726");
/* 126 */     byte[] bytes = new byte[(int)file.length()];
/*     */     
/* 128 */     try (FileInputStream fis = new FileInputStream(file)) {
/* 129 */       fis.read(bytes);
/*     */     } 
/* 131 */     G726NormalDecoder decoder = new G726NormalDecoder();
/* 132 */     int totalFrames = bytes.length / FRAME_SIZE;
/* 133 */     for (int i = 0; i < totalFrames; i++) {
/*     */       
/* 135 */       int start = i * FRAME_SIZE;
/* 136 */       int end = start + FRAME_SIZE;
/*     */ 
/*     */       
/* 139 */       if (end > bytes.length) {
/* 140 */         end = bytes.length;
/*     */       }
/*     */ 
/*     */       
/* 144 */       byte[] frame = new byte[FRAME_SIZE];
/* 145 */       System.arraycopy(bytes, start, frame, 0, Math.min(FRAME_SIZE, end - start));
/* 146 */       decoder.decode(frame, new G726Decoder.Event()
/*     */           {
/*     */             public void onAudioDecodeFrame(byte[] audioBytes) {
/* 149 */               System.out.println("audioBytes.length:" + audioBytes.length);
/* 150 */               audioPlayTrack.play(audioBytes);
/*     */             }
/*     */           });
/*     */     } 
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/viewer/AudioPlayTrack.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */