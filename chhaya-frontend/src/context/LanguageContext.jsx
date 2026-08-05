import { createContext, useContext, useState } from "react";

const translations = {
  en: {
    referenceSources: "Reference sources",
    studyGuides: "Study guides",
    styleLibrary: "Style library",
    analytics: "Analytics & Progress",
    examPapers: "Past Exam Papers",
    addSource: "Add reference source",
    newGuide: "New study guide",
    topic: "Topic",
    teachingStyle: "Teaching style",
    depthAndLanguage: "Depth and language",
    formulaSheet: "Formula sheet",
    banglaVersion: "Bangla version",
    generateGuide: "Generate study guide",
    searchPlaceholder: "Search topics, teachers...",
    cancel: "Cancel",
    rename: "Rename",
    delete: "Delete",
    saveToLibrary: "Save to style library",
    ready: "Ready",
    analysing: "Analysing",
    generating: "Generating",
    needsAttention: "Needs attention",
    failed: "Failed",
  },
  bn: {
    referenceSources: "রেফারেন্স সোর্সসমূহ",
    studyGuides: "স্টাডি গাইডসমূহ",
    styleLibrary: "স্টাইল লাইব্রেরি",
    analytics: "অ্যানালিটিক্স ও অগ্রগতি",
    examPapers: "বিগত বছরের প্রশ্ন",
    addSource: "রেফারেন্স সোর্স যোগ করুন",
    newGuide: "নতুন স্টাডি গাইড",
    topic: "বিষয় / টপিক",
    teachingStyle: "টিচিং স্টাইল",
    depthAndLanguage: "গভীরতা ও ভাষা",
    formulaSheet: "সূত্র তালিকা (ফর্মুলা শিট)",
    banglaVersion: "বাংলা সংস্করণ",
    generateGuide: "স্টাডি গাইড তৈরি করুন",
    searchPlaceholder: "টপিক বা শিক্ষক খুঁজুন...",
    cancel: "বাতিল",
    rename: "পুনরায় নামকরণ",
    delete: "মুছে ফেলুন",
    saveToLibrary: "লাইব্রেরিতে সংরক্ষণ করুন",
    ready: "প্রস্তুত",
    analysing: "বিশ্লেষণ করা হচ্ছে",
    generating: "তৈরি করা হচ্ছে",
    needsAttention: "মনোযোগ প্রয়োজন",
    failed: "ব্যর্থ",
  },
};

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState("en");

  function t(key) {
    return translations[lang]?.[key] || translations["en"]?.[key] || key;
  }

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}
