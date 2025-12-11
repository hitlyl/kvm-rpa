/*     */ package com.hiklife.svc.console;
/*     */ import java.util.ArrayList;
/*     */ import java.util.HashMap;
/*     */ import java.util.List;
/*     */ import java.util.Map;

import refs.com.hiklife.svc.core.protocol.normal.KeyEventPacket;
import refs.com.hiklife.svc.util.HexUtils;
/*     */ 
/*     */ public class EnKeyMap
/*     */ {
/*     */   public static final String EN_CHARS = "^[a-zA-Z0-9\\s!\"#$%&'()*+,-./:;<=>?@\\[\\\\\\]^_`{|}~ ]*$";
/*  13 */   private static final Map<Character, Integer> KEY_MAP = new HashMap<>();
/*  14 */   private static final Map<Character, Integer> KEY_MAP_SHIFT = new HashMap<>();
/*     */   static {
/*  16 */     initializeKeyMap();
/*     */   }
/*     */   public static List<KeyEventPacket> str2KeyEvent(String chars) throws Exception {
/*  19 */     List<KeyEventPacket> keyEventPackets = new ArrayList<>();
/*  20 */     if (HexUtils.isEmpty(chars)) {
/*  21 */       return keyEventPackets;
/*     */     }
/*  23 */     if (chars.matches("^[a-zA-Z0-9\\s!\"#$%&'()*+,-./:;<=>?@\\[\\\\\\]^_`{|}~ ]*$")) {
/*  24 */       for (char c : chars.toCharArray()) {
/*  25 */         if (KEY_MAP.containsKey(Character.valueOf(c))) {
/*  26 */           Integer key = KEY_MAP.get(Character.valueOf(c));
/*  27 */           if (key != null) {
/*  28 */             keyEventPackets.add(new KeyEventPacket(1, key.intValue()));
/*  29 */             keyEventPackets.add(new KeyEventPacket(0, key.intValue()));
/*     */           } 
/*  31 */         } else if (KEY_MAP_SHIFT.containsKey(Character.valueOf(c))) {
/*  32 */           Integer key = KEY_MAP_SHIFT.get(Character.valueOf(c));
/*  33 */           if (key != null) {
/*  34 */             keyEventPackets.add(new KeyEventPacket(1, 65505));
/*  35 */             keyEventPackets.add(new KeyEventPacket(1, key.intValue()));
/*  36 */             keyEventPackets.add(new KeyEventPacket(0, key.intValue()));
/*  37 */             keyEventPackets.add(new KeyEventPacket(0, 65505));
/*     */           } 
/*     */         } 
/*     */       } 
/*     */     } else {
/*     */       
/*  43 */       throw new Exception("包含非支持字符,校验规则为:^[a-zA-Z0-9\\s!\"#$%&'()*+,-./:;<=>?@\\[\\\\\\]^_`{|}~ ]*$");
/*     */     } 
/*  45 */     return keyEventPackets;
/*     */   }
/*     */   
/*     */   private static void initializeKeyMap() {
/*  49 */     KEY_MAP.put(Character.valueOf('a'), Integer.valueOf(65));
/*  50 */     KEY_MAP.put(Character.valueOf('b'), Integer.valueOf(66));
/*  51 */     KEY_MAP.put(Character.valueOf('c'), Integer.valueOf(67));
/*  52 */     KEY_MAP.put(Character.valueOf('d'), Integer.valueOf(68));
/*  53 */     KEY_MAP.put(Character.valueOf('e'), Integer.valueOf(69));
/*  54 */     KEY_MAP.put(Character.valueOf('f'), Integer.valueOf(70));
/*  55 */     KEY_MAP.put(Character.valueOf('g'), Integer.valueOf(71));
/*  56 */     KEY_MAP.put(Character.valueOf('h'), Integer.valueOf(72));
/*  57 */     KEY_MAP.put(Character.valueOf('i'), Integer.valueOf(73));
/*  58 */     KEY_MAP.put(Character.valueOf('j'), Integer.valueOf(74));
/*  59 */     KEY_MAP.put(Character.valueOf('k'), Integer.valueOf(75));
/*  60 */     KEY_MAP.put(Character.valueOf('l'), Integer.valueOf(76));
/*  61 */     KEY_MAP.put(Character.valueOf('m'), Integer.valueOf(77));
/*  62 */     KEY_MAP.put(Character.valueOf('n'), Integer.valueOf(78));
/*  63 */     KEY_MAP.put(Character.valueOf('o'), Integer.valueOf(79));
/*  64 */     KEY_MAP.put(Character.valueOf('p'), Integer.valueOf(80));
/*  65 */     KEY_MAP.put(Character.valueOf('q'), Integer.valueOf(81));
/*  66 */     KEY_MAP.put(Character.valueOf('r'), Integer.valueOf(82));
/*  67 */     KEY_MAP.put(Character.valueOf('s'), Integer.valueOf(83));
/*  68 */     KEY_MAP.put(Character.valueOf('t'), Integer.valueOf(84));
/*  69 */     KEY_MAP.put(Character.valueOf('u'), Integer.valueOf(85));
/*  70 */     KEY_MAP.put(Character.valueOf('v'), Integer.valueOf(86));
/*  71 */     KEY_MAP.put(Character.valueOf('w'), Integer.valueOf(87));
/*  72 */     KEY_MAP.put(Character.valueOf('x'), Integer.valueOf(88));
/*  73 */     KEY_MAP.put(Character.valueOf('y'), Integer.valueOf(89));
/*  74 */     KEY_MAP.put(Character.valueOf('z'), Integer.valueOf(90));
/*  75 */     KEY_MAP_SHIFT.put(Character.valueOf('A'), Integer.valueOf(65));
/*  76 */     KEY_MAP_SHIFT.put(Character.valueOf('b'), Integer.valueOf(66));
/*  77 */     KEY_MAP_SHIFT.put(Character.valueOf('C'), Integer.valueOf(67));
/*  78 */     KEY_MAP_SHIFT.put(Character.valueOf('D'), Integer.valueOf(68));
/*  79 */     KEY_MAP_SHIFT.put(Character.valueOf('E'), Integer.valueOf(69));
/*  80 */     KEY_MAP_SHIFT.put(Character.valueOf('F'), Integer.valueOf(70));
/*  81 */     KEY_MAP_SHIFT.put(Character.valueOf('G'), Integer.valueOf(71));
/*  82 */     KEY_MAP_SHIFT.put(Character.valueOf('H'), Integer.valueOf(72));
/*  83 */     KEY_MAP_SHIFT.put(Character.valueOf('I'), Integer.valueOf(73));
/*  84 */     KEY_MAP_SHIFT.put(Character.valueOf('J'), Integer.valueOf(74));
/*  85 */     KEY_MAP_SHIFT.put(Character.valueOf('K'), Integer.valueOf(75));
/*  86 */     KEY_MAP_SHIFT.put(Character.valueOf('L'), Integer.valueOf(76));
/*  87 */     KEY_MAP_SHIFT.put(Character.valueOf('M'), Integer.valueOf(77));
/*  88 */     KEY_MAP_SHIFT.put(Character.valueOf('N'), Integer.valueOf(78));
/*  89 */     KEY_MAP_SHIFT.put(Character.valueOf('O'), Integer.valueOf(79));
/*  90 */     KEY_MAP_SHIFT.put(Character.valueOf('P'), Integer.valueOf(80));
/*  91 */     KEY_MAP_SHIFT.put(Character.valueOf('Q'), Integer.valueOf(81));
/*  92 */     KEY_MAP_SHIFT.put(Character.valueOf('R'), Integer.valueOf(82));
/*  93 */     KEY_MAP_SHIFT.put(Character.valueOf('S'), Integer.valueOf(83));
/*  94 */     KEY_MAP_SHIFT.put(Character.valueOf('T'), Integer.valueOf(84));
/*  95 */     KEY_MAP_SHIFT.put(Character.valueOf('U'), Integer.valueOf(85));
/*  96 */     KEY_MAP_SHIFT.put(Character.valueOf('V'), Integer.valueOf(86));
/*  97 */     KEY_MAP_SHIFT.put(Character.valueOf('W'), Integer.valueOf(87));
/*  98 */     KEY_MAP_SHIFT.put(Character.valueOf('X'), Integer.valueOf(88));
/*  99 */     KEY_MAP_SHIFT.put(Character.valueOf('Y'), Integer.valueOf(89));
/* 100 */     KEY_MAP_SHIFT.put(Character.valueOf('Z'), Integer.valueOf(90));
/*     */     
/* 102 */     KEY_MAP.put(Character.valueOf('0'), Integer.valueOf(48));
/* 103 */     KEY_MAP.put(Character.valueOf('1'), Integer.valueOf(49));
/* 104 */     KEY_MAP.put(Character.valueOf('2'), Integer.valueOf(50));
/* 105 */     KEY_MAP.put(Character.valueOf('3'), Integer.valueOf(51));
/* 106 */     KEY_MAP.put(Character.valueOf('4'), Integer.valueOf(52));
/* 107 */     KEY_MAP.put(Character.valueOf('5'), Integer.valueOf(53));
/* 108 */     KEY_MAP.put(Character.valueOf('6'), Integer.valueOf(54));
/* 109 */     KEY_MAP.put(Character.valueOf('7'), Integer.valueOf(55));
/* 110 */     KEY_MAP.put(Character.valueOf('8'), Integer.valueOf(56));
/* 111 */     KEY_MAP.put(Character.valueOf('9'), Integer.valueOf(57));
/* 112 */     KEY_MAP_SHIFT.put(Character.valueOf('!'), Integer.valueOf(49));
/* 113 */     KEY_MAP_SHIFT.put(Character.valueOf('@'), Integer.valueOf(50));
/* 114 */     KEY_MAP_SHIFT.put(Character.valueOf('#'), Integer.valueOf(51));
/* 115 */     KEY_MAP_SHIFT.put(Character.valueOf('$'), Integer.valueOf(52));
/* 116 */     KEY_MAP_SHIFT.put(Character.valueOf('%'), Integer.valueOf(53));
/* 117 */     KEY_MAP_SHIFT.put(Character.valueOf('^'), Integer.valueOf(54));
/* 118 */     KEY_MAP_SHIFT.put(Character.valueOf('&'), Integer.valueOf(55));
/* 119 */     KEY_MAP_SHIFT.put(Character.valueOf('*'), Integer.valueOf(56));
/* 120 */     KEY_MAP_SHIFT.put(Character.valueOf('('), Integer.valueOf(57));
/* 121 */     KEY_MAP_SHIFT.put(Character.valueOf(')'), Integer.valueOf(48));
/*     */     
/* 123 */     KEY_MAP.put(Character.valueOf(' '), Integer.valueOf(32));
/* 124 */     KEY_MAP.put(Character.valueOf('`'), Integer.valueOf(96));
/* 125 */     KEY_MAP.put(Character.valueOf('-'), Integer.valueOf(45));
/* 126 */     KEY_MAP.put(Character.valueOf('='), Integer.valueOf(61));
/* 127 */     KEY_MAP.put(Character.valueOf('['), Integer.valueOf(91));
/* 128 */     KEY_MAP.put(Character.valueOf(']'), Integer.valueOf(93));
/* 129 */     KEY_MAP.put(Character.valueOf('\\'), Integer.valueOf(92));
/* 130 */     KEY_MAP.put(Character.valueOf(';'), Integer.valueOf(59));
/* 131 */     KEY_MAP.put(Character.valueOf('\''), Integer.valueOf(34));
/* 132 */     KEY_MAP.put(Character.valueOf(','), Integer.valueOf(44));
/* 133 */     KEY_MAP.put(Character.valueOf('.'), Integer.valueOf(46));
/* 134 */     KEY_MAP.put(Character.valueOf('/'), Integer.valueOf(47));
/*     */     
/* 136 */     KEY_MAP_SHIFT.put(Character.valueOf('~'), Integer.valueOf(96));
/* 137 */     KEY_MAP_SHIFT.put(Character.valueOf('_'), Integer.valueOf(45));
/* 138 */     KEY_MAP_SHIFT.put(Character.valueOf('+'), Integer.valueOf(61));
/* 139 */     KEY_MAP_SHIFT.put(Character.valueOf('{'), Integer.valueOf(91));
/* 140 */     KEY_MAP_SHIFT.put(Character.valueOf('}'), Integer.valueOf(93));
/* 141 */     KEY_MAP_SHIFT.put(Character.valueOf('|'), Integer.valueOf(92));
/* 142 */     KEY_MAP_SHIFT.put(Character.valueOf(':'), Integer.valueOf(59));
/* 143 */     KEY_MAP_SHIFT.put(Character.valueOf('"'), Integer.valueOf(34));
/* 144 */     KEY_MAP_SHIFT.put(Character.valueOf('<'), Integer.valueOf(44));
/* 145 */     KEY_MAP_SHIFT.put(Character.valueOf('>'), Integer.valueOf(46));
/* 146 */     KEY_MAP_SHIFT.put(Character.valueOf('?'), Integer.valueOf(47));
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/console/EnKeyMap.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */