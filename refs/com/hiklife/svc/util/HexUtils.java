/*     */ package com.hiklife.svc.util;
/*     */ 
/*     */ import java.nio.charset.StandardCharsets;
/*     */ import java.util.regex.Pattern;
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
/*     */ public class HexUtils
/*     */ {
/*     */   private static final String HEXSTRING = "0123456789ABCDEF";
/*     */   public static final String EMPTY = "";
/*     */   
/*     */   public static byte[] hexStringToBytes(String hexString) {
/*  25 */     byte[] combhexBt = null;
/*  26 */     if (isNotBlank(hexString)) {
/*  27 */       if (hexString.length() % 2 != 0) {
/*  28 */         hexString = "0" + hexString;
/*     */       }
/*     */       
/*  31 */       if (Pattern.compile("[A-Fa-f0-9]+").matcher(hexString).find()) {
/*  32 */         String hexStrLow = hexString.toUpperCase();
/*  33 */         byte[] strBytes = hexStrLow.getBytes();
/*  34 */         byte[] hexBytes = new byte[strBytes.length];
/*  35 */         combhexBt = new byte[strBytes.length / 2]; int i;
/*  36 */         for (i = 0; i < strBytes.length; i++) {
/*  37 */           if (strBytes[i] >= 48 && strBytes[i] <= 57) {
/*  38 */             hexBytes[i] = (byte)(strBytes[i] - 48);
/*  39 */           } else if (strBytes[i] >= 65 && strBytes[i] <= 70) {
/*  40 */             hexBytes[i] = (byte)(strBytes[i] - 55);
/*     */           } 
/*     */         } 
/*     */         
/*  44 */         for (i = 0; i < combhexBt.length; i++) {
/*  45 */           int pos = i * 2;
/*  46 */           combhexBt[i] = (byte)(hexBytes[pos] << 4 | hexBytes[pos + 1]);
/*     */         } 
/*     */       } 
/*     */     } 
/*  50 */     return combhexBt;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static String bytesToHexString(byte[] combhexBt) {
/*  60 */     if (combhexBt == null || combhexBt.length == 0) {
/*  61 */       return null;
/*     */     }
/*  63 */     StringBuilder sb = new StringBuilder(combhexBt.length * 2);
/*  64 */     for (byte b : combhexBt) {
/*  65 */       sb.append("0123456789ABCDEF".charAt((b & 0xF0) >> 4));
/*  66 */       sb.append("0123456789ABCDEF".charAt(b & 0xF));
/*     */     } 
/*  68 */     return sb.toString();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static String bytesToHexString(byte[] combhexBt, int off, int length) {
/*  80 */     if (combhexBt == null || combhexBt.length == 0) {
/*  81 */       return null;
/*     */     }
/*  83 */     StringBuilder sb = new StringBuilder(combhexBt.length * 2);
/*  84 */     for (int i = off; i < length; i++) {
/*  85 */       sb.append("0123456789ABCDEF".charAt((combhexBt[i] & 0xF0) >> 4));
/*  86 */       sb.append("0123456789ABCDEF".charAt(combhexBt[i] & 0xF));
/*     */     } 
/*  88 */     return sb.toString();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static byte[] intToBytesBigEndian(int value) {
/*  99 */     byte[] src = new byte[4];
/* 100 */     src[0] = (byte)(value >> 24 & 0xFF);
/* 101 */     src[1] = (byte)(value >> 16 & 0xFF);
/* 102 */     src[2] = (byte)(value >> 8 & 0xFF);
/* 103 */     src[3] = (byte)(value & 0xFF);
/* 104 */     return src;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static byte[] intToBytesLittleEndian(int value) {
/* 114 */     byte[] src = new byte[4];
/* 115 */     src[3] = (byte)(value >> 24 & 0xFF);
/* 116 */     src[2] = (byte)(value >> 16 & 0xFF);
/* 117 */     src[1] = (byte)(value >> 8 & 0xFF);
/* 118 */     src[0] = (byte)(value & 0xFF);
/* 119 */     return src;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static int bytesToIntBigEndian(byte[] src, int offset) {
/* 131 */     int value = (src[offset] & 0xFF) << 24 | (src[offset + 1] & 0xFF) << 16 | (src[offset + 2] & 0xFF) << 8 | src[offset + 3] & 0xFF;
/*     */ 
/*     */ 
/*     */     
/* 135 */     return value;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static int bytesToIntLittle(byte[] src, int offset) {
/* 147 */     int value = src[offset] & 0xFF | (src[offset + 1] & 0xFF) << 8 | (src[offset + 2] & 0xFF) << 16 | (src[offset + 3] & 0xFF) << 24;
/*     */ 
/*     */ 
/*     */     
/* 151 */     return value;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static int registerToUnsignedShort(byte[] bytes) {
/* 163 */     return (bytes[0] & 0xFF) << 8 | bytes[1] & 0xFF;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static int registerToUnsignedShort(byte[] bytes, int off) {
/* 175 */     return (bytes[off] & 0xFF) << 8 | bytes[off + 1] & 0xFF;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static byte[] unsignedShortToRegister(int v) {
/* 186 */     byte[] register = new byte[2];
/* 187 */     register[0] = (byte)(0xFF & v >> 8);
/* 188 */     register[1] = (byte)(0xFF & v);
/* 189 */     return register;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static short registerToShort(byte[] bytes, int idx) {
/* 201 */     return (short)(bytes[idx] << 8 | bytes[idx + 1] & 0xFF);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static byte[] signedShortToRegister(short s) {
/* 211 */     return new byte[] { (byte)(s >> 8), (byte)s };
/*     */   }
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
/*     */   public static int registersToInt(byte[] bytes) {
/* 224 */     return (bytes[0] & 0xFF) << 24 | (bytes[1] & 0xFF) << 16 | (bytes[2] & 0xFF) << 8 | bytes[3] & 0xFF;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static int registersToInt(byte[] bytes, int off) {
/* 235 */     return (bytes[off] & 0xFF) << 24 | (bytes[1 + off] & 0xFF) << 16 | (bytes[2 + off] & 0xFF) << 8 | bytes[3 + off] & 0xFF;
/*     */   }
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
/*     */   public static String bytesToAscii(byte[] bytes, int offset, int dateLen) {
/* 248 */     if (bytes == null || bytes.length == 0 || offset < 0 || dateLen <= 0) {
/* 249 */       return null;
/*     */     }
/* 251 */     if (offset >= bytes.length || bytes.length - offset < dateLen) {
/* 252 */       return null;
/*     */     }
/*     */ 
/*     */     
/* 256 */     byte[] data = new byte[dateLen];
/* 257 */     System.arraycopy(bytes, offset, data, 0, dateLen);
/* 258 */     String asciiStr = new String(data, StandardCharsets.UTF_8);
/* 259 */     asciiStr = asciiStr.trim();
/* 260 */     return asciiStr;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static String bytesToAscii(byte[] bytes, int dateLen) {
/* 271 */     return bytesToAscii(bytes, 0, dateLen);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static byte[] getBooleanArray(byte b) {
/* 280 */     byte[] array = new byte[8];
/* 281 */     for (int i = 7; i >= 0; i--) {
/* 282 */       array[i] = (byte)(b & 0x1);
/* 283 */       b = (byte)(b >> 1);
/*     */     } 
/* 285 */     return array;
/*     */   }
/*     */   public static boolean isBlank(String str) {
/* 288 */     return !isNotBlank(str);
/*     */   }
/*     */   public static boolean isNotBlank(String str) {
/* 291 */     if (str == null || str.isEmpty()) {
/* 292 */       return false;
/*     */     }
/* 294 */     int length = str.length();
/* 295 */     for (int i = 0; i < length; i++) {
/* 296 */       if (!Character.isWhitespace(str.charAt(i))) {
/* 297 */         return true;
/*     */       }
/*     */     } 
/* 300 */     return false;
/*     */   }
/*     */   
/*     */   public static boolean isEmpty(String str) {
/* 304 */     return (str == null || str.isEmpty());
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/util/HexUtils.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */