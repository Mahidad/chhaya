import { visit } from "unist-util-visit";

// react-markdown v10 won't invoke components.text -- component overrides
// only fire for real element tag names. This wraps every text node in a
// <htext> element so components={{ htext: HighlightableText }} actually fires.
//
// IMPORTANT: every text node gets wrapped, including whitespace-only ones.
// AnnotatableText.jsx's HighlightableText keeps a running character count
// (`charCounter`) as it walks through each wrapped node, and that count
// has to land on the exact same total as getSelectionOffset() (which
// counts literally every character in the rendered DOM, whitespace
// included). An earlier version of this file skipped whitespace-only text
// nodes to avoid wrapping pointless empty elements -- but that meant
// charCounter silently fell behind the real DOM offset by exactly the
// amount of skipped whitespace, and that gap grew for every paragraph/
// list item/heading boundary in the document. The visible symptom was
// highlights (and sticky notes, before those were removed) landing a few
// characters into the next word instead of exactly on the selected text,
// worse the further down the page you selected. Wrapping every text node
// -- whitespace included -- keeps the two counters perfectly in sync.
export default function rehypeTextify() {
  return (tree) => {
    visit(tree, "text", (node, index, parent) => {
      if (!parent || parent.tagName === "htext" || parent.tagName === "script" || parent.tagName === "style") return;
      if (!node.value) return; // still skip truly empty ("") nodes, nothing to count or wrap
      parent.children[index] = {
        type: "element",
        tagName: "htext",
        properties: {},
        children: [node],
      };
    });
  };
}
