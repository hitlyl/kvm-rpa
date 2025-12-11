/*     */ package com.hiklife.svc.core.net;
/*     */ import org.apache.mina.core.buffer.IoBuffer;
/*     */ import org.apache.mina.core.session.IoSession;
/*     */ import org.apache.mina.filter.codec.CumulativeProtocolDecoder;
/*     */ import org.apache.mina.filter.codec.ProtocolCodecFactory;
/*     */ import org.apache.mina.filter.codec.ProtocolDecoder;
/*     */ import org.apache.mina.filter.codec.ProtocolDecoderOutput;
/*     */ import org.apache.mina.filter.codec.ProtocolEncoder;
/*     */ import org.apache.mina.filter.codec.ProtocolEncoderOutput;
/*     */ import org.slf4j.Logger;
/*     */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.core.net.ProtocolCodec;
import refs.com.hiklife.svc.core.protocol.ProtocolHandler;
import refs.com.hiklife.svc.core.protocol.baseinfo.DevicePacket;
import refs.com.hiklife.svc.core.protocol.normal.AudioFramePacket;
import refs.com.hiklife.svc.core.protocol.normal.ReadNormalType;
import refs.com.hiklife.svc.core.protocol.normal.VideoFramePacket;
import refs.com.hiklife.svc.core.protocol.security.SecurityType;
import refs.com.hiklife.svc.core.protocol.vm.VMWritePacket;
import refs.com.hiklife.svc.util.HexUtils;
/*     */ 
/*     */ public class ProtocolCodec implements ProtocolCodecFactory {
/*  22 */   private static final Logger log = LoggerFactory.getLogger(ProtocolCodec.class);
/*     */ 
/*     */   
/*     */   private static final int MAX_IO_BUFFER_SIZE = 31457280;
/*     */ 
/*     */   
/*     */   private static final int MAX_RECEIVE_BUFFER_SIZE = 30720000;
/*     */   
/*     */   private static final int MESSAGE_MIN_LENGTH = 4;
/*     */   
/*     */   private boolean isChanlleng = false;
/*     */ 
/*     */   
/*     */   public ProtocolEncoder getEncoder(IoSession ioSession) {
/*  36 */     return new ProtocolEncoder()
/*     */       {
/*     */         public void encode(IoSession session, Object message, ProtocolEncoderOutput out) {
/*  39 */           byte[] byteMsg = (byte[])message;
/*  40 */           IoBuffer buffer = IoBuffer.allocate(byteMsg.length, false);
/*  41 */           buffer.put(byteMsg);
/*  42 */           buffer.flip();
/*  43 */           out.write(buffer);
/*     */         }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */         
/*     */         public void dispose(IoSession session) {}
/*     */       };
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public ProtocolDecoder getDecoder(final IoSession ioSession) {
/*  61 */     return (ProtocolDecoder)new CumulativeProtocolDecoder()
/*     */       {
/*     */         protected boolean doDecode(IoSession session, IoBuffer in, ProtocolDecoderOutput out) {
/*  64 */           int remainingLength = in.remaining();
/*  65 */           if (in.capacity() > 31457280) {
/*  66 */             ProtocolCodec.log.error("ioBuffer.capacity is: {},iobuffer too big,clear and close session", Integer.valueOf(in.capacity()));
/*     */             
/*  68 */             in.position(in.limit());
/*     */             
/*  70 */             ioSession.closeNow();
/*  71 */             return false;
/*     */           } 
/*  73 */           if (remainingLength > 30720000) {
/*  74 */             ProtocolCodec.log.error("data from session {} can not decode,message dropped", Long.valueOf(ioSession.getId()));
/*  75 */             ProtocolCodec.log.error("data from session {} buffer size is {}", Long.valueOf(ioSession.getId()), Integer.valueOf(in.remaining()));
/*     */             
/*  77 */             in.position(in.limit());
/*  78 */             return false;
/*     */           } 
/*     */           
/*  81 */           ProtocolHandler handler = (ProtocolHandler)ioSession.getAttribute("handler");
/*  82 */           if (handler.getSession() == null) {
/*  83 */             handler.setSession(session);
/*     */           }
/*  85 */           if (handler.isNormalMessage() || handler.isVersionMessage() || handler.isCentralizeMessage() || handler.isSecurityTypesMessage()) {
/*     */             
/*  87 */             in.mark();
/*  88 */             byte[] byteTemp = new byte[remainingLength];
/*     */             
/*  90 */             in.get(byteTemp);
/*  91 */             in.position(in.position());
/*  92 */             int length = 0;
/*  93 */             if (handler.isVersionMessage()) {
/*  94 */               length = ProtocolCodec.this.decodeVersionMessage(byteTemp);
/*  95 */             } else if (handler.isNormalMessage()) {
/*  96 */               length = ProtocolCodec.this.decodeMessage(byteTemp);
/*  97 */             } else if (handler.isCentralizeMessage()) {
/*  98 */               length = ProtocolCodec.this.decodeCentralizeMessage(byteTemp);
/*  99 */             } else if (handler.isSecurityTypesMessage()) {
/* 100 */               length = ProtocolCodec.this.decodeSecurityTypesMessage(byteTemp);
/*     */             } 
/*     */ 
/*     */             
/* 104 */             in.reset();
/* 105 */             if (length > 0) {
/* 106 */               byte[] arrayOfByte = new byte[length];
/* 107 */               in.get(arrayOfByte, 0, length);
/* 108 */               out.write(arrayOfByte);
/* 109 */               return true;
/*     */             } 
/* 111 */             return false;
/*     */           } 
/*     */           
/* 114 */           byte[] bytes = new byte[remainingLength];
/* 115 */           in.get(bytes, 0, remainingLength);
/* 116 */           out.write(bytes);
/* 117 */           return false;
/*     */         }
/*     */       };
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private int decodeVersionMessage(byte[] msgBytes) {
/* 129 */     if (msgBytes.length < 12) {
/* 130 */       return 0;
/*     */     }
/* 132 */     int size = DevicePacket.length(msgBytes);
/* 133 */     if (msgBytes.length == size) {
/* 134 */       return size;
/*     */     }
/*     */     
/* 137 */     int length = SecurityType.length(msgBytes, size);
/* 138 */     if (msgBytes.length < length + size) {
/* 139 */       return size;
/*     */     }
/* 141 */     return length + size;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private int decodeCentralizeMessage(byte[] msgBytes) {
/* 152 */     int size = msgBytes.length;
/* 153 */     int total = 17;
/* 154 */     if (size == total) {
/* 155 */       this.isChanlleng = true;
/* 156 */       return 1;
/*     */     } 
/* 158 */     if (this.isChanlleng) {
/* 159 */       this.isChanlleng = false;
/* 160 */       return total - 1;
/*     */     } 
/* 162 */     return 0;
/*     */   }
/*     */   private int decodeSecurityTypesMessage(byte[] msgBytes) {
/* 165 */     int length = SecurityType.length(msgBytes);
/* 166 */     if (msgBytes.length < length) {
/* 167 */       return 0;
/*     */     }
/* 169 */     return length;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private int decodeMessage(byte[] msgBytes) {
/*     */     int videoParamSize, keyStatusSize, audioParamSize;
/* 178 */     if (msgBytes.length < 4) {
/* 179 */       return 0;
/*     */     }
/* 181 */     ReadNormalType type = ReadNormalType.parse(msgBytes[0]);
/* 182 */     int size = msgBytes.length;
/* 183 */     switch (type)
/*     */     
/*     */     { case FrameBufferUpdate:
/* 186 */         if (msgBytes[3] == 0) {
/* 187 */           size = 4;
/* 188 */         } else if (msgBytes[3] == 1) {
/* 189 */           if (size < 20) {
/* 190 */             size = 0;
/*     */           } else {
/* 192 */             int videoSize = VideoFramePacket.length01(msgBytes);
/* 193 */             if (msgBytes.length < videoSize) {
/* 194 */               size = 0;
/*     */             } else {
/* 196 */               size = videoSize;
/* 197 */               log.trace("Retrieved the video");
/*     */             } 
/*     */           } 
/* 200 */         } else if (msgBytes[3] == 2) {
/* 201 */           if (size < 20) {
/* 202 */             size = 0;
/*     */           } else {
/* 204 */             int videoSize = VideoFramePacket.length02(msgBytes);
/* 205 */             if (msgBytes.length < videoSize) {
/* 206 */               size = 0;
/*     */             } else {
/* 208 */               size = videoSize;
/* 209 */               log.trace("Retrieved the video 2");
/*     */             } 
/*     */           } 
/*     */         } 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */       
/*     */       case SetColourMapEntries:
/*     */       case Bell:
/*     */       case ServerCutText:
/* 289 */         return size;case AudioBufferUpdate: if (msgBytes.length < 12) { size = 0; } else { int audioSize = AudioFramePacket.length(msgBytes); if (msgBytes.length < audioSize) { size = 0; } else { size = audioSize; log.trace("Retrieved the audio"); }  } case VMRead: return size;case VMWrite: if (msgBytes.length < 15) { size = 0; } else { int writeSize = VMWritePacket.length(msgBytes); if (msgBytes.length < writeSize) { size = 0; } else { size = writeSize; }  } case VideoParam: videoParamSize = 36; if (msgBytes.length < videoParamSize) { size = 0; } else { size = videoParamSize; } case KeyStatus: keyStatusSize = 5; if (msgBytes.length < keyStatusSize) { size = 0; } else { size = keyStatusSize; } case DeviceInfo: return size;case AudioParam: audioParamSize = 8; if (msgBytes.length < audioParamSize) { size = 0; } else { size = audioParamSize; } case MouseType: size = 4;case VideoLevel: return size;
/*     */       case BroadcastStatus:
/*     */         size = 68;
/*     */       case BroadcastSetStatus:
/* 293 */         size = 68; }  log.error("decodeMessage error:{}", HexUtils.bytesToHexString(msgBytes)); return size; } public static void main(String[] agrs) { String hexStr = "0000000100000000078004B0000001070000007B0000000161E2623BFF00000300000300000300000300002464769F59B76690121CC7CA996FE51FCA24F66FF6BFFFBECBC8A9E1BB034EBFEF857935542E84D84F32E63FA4512F3089FEC6F89B9B00000300000300000300000300000300000300000300000300000300000300000300000300000300000300001A10040000000000005800012A00D0F44C0081002E109B43D01009B308AA40C7839F8029931C1A31AB688812A3DD011B44A8289B924E20A90185880089F1480D2888C34C100800B5B8000C42E11A2A1019A191808088080808080801C4DE301F21830000000100000000078004B00000010700";
/* 294 */     byte[] bytes = HexUtils.hexStringToBytes(hexStr);
/* 295 */     (new ProtocolCodec()).decodeMessage(bytes); }
/*     */ 
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/net/ProtocolCodec.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */