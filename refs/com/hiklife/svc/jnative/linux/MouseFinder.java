/*    */ package com.hiklife.svc.jnative.linux;
/*    */ 
/*    */ import java.io.BufferedReader;
/*    */ import java.io.FileReader;
/*    */ import java.io.IOException;
/*    */ import java.util.ArrayList;
/*    */ import java.util.List;
/*    */ import java.util.regex.Matcher;
/*    */ import java.util.regex.Pattern;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class MouseFinder
/*    */ {
/*    */   public static List<String> findMouseEventPaths() throws IOException {
/* 17 */     List<String> mousePaths = new ArrayList<>();
/*    */     
/* 19 */     try (BufferedReader reader = new BufferedReader(new FileReader("/proc/bus/input/devices"))) {
/*    */       
/* 21 */       String currentHandlers = null;
/* 22 */       boolean isMouseDevice = false;
/*    */       String line;
/* 24 */       while ((line = reader.readLine()) != null) {
/* 25 */         if (line.startsWith("H: Handlers=")) {
/* 26 */           currentHandlers = line.substring(12);
/*    */           
/* 28 */           isMouseDevice = currentHandlers.toLowerCase().contains("mouse"); continue;
/* 29 */         }  if (line.startsWith("N: Name=")) {
/* 30 */           String name = line.substring(8).replace("\"", "").toLowerCase();
/*    */           
/* 32 */           if (name.contains("mouse") || name.contains("trackpoint"))
/* 33 */             isMouseDevice = true;  continue;
/*    */         } 
/* 35 */         if (line.trim().isEmpty() && isMouseDevice && currentHandlers != null) {
/*    */           
/* 37 */           Pattern pattern = Pattern.compile("event(\\d+)");
/* 38 */           Matcher matcher = pattern.matcher(currentHandlers);
/* 39 */           if (matcher.find()) {
/* 40 */             String eventPath = "/dev/input/event" + matcher.group(1);
/* 41 */             mousePaths.add(eventPath);
/*    */           } 
/* 43 */           currentHandlers = null;
/* 44 */           isMouseDevice = false;
/*    */         } 
/*    */       } 
/*    */     } 
/*    */     
/* 49 */     return mousePaths;
/*    */   }
/*    */   
/*    */   public static void main(String[] args) {
/*    */     try {
/* 54 */       List<String> mousePaths = findMouseEventPaths();
/* 55 */       if (mousePaths.isEmpty()) {
/* 56 */         System.out.println("未找到鼠标设备");
/*    */       } else {
/* 58 */         System.out.println("找到的鼠标设备路径:");
/* 59 */         for (String path : mousePaths) {
/* 60 */           System.out.println("  " + path);
/*    */         }
/*    */       } 
/* 63 */     } catch (IOException e) {
/* 64 */       System.err.println("错误: " + e.getMessage());
/*    */     } 
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/jnative/linux/MouseFinder.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */