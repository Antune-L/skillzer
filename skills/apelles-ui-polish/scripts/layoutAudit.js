() => {
  const TOLERANCE_PX = 1;
  const MAX_FINDINGS = 25;
  const MAX_TEXT_LENGTH = 60;
  const MAX_SELECTOR_ANCESTORS = 4;
  const MAX_SELECTOR_CLASSES = 2;
  const MIN_TARGET_PX = 24;
  const MIN_VISIBLE_SIZE_PX = 2;
  const SLOW_MOTION_MS = 400;
  const MS_PER_SECOND = 1000;
  const MIN_NUMERIC_DIGITS = 2;
  const NUMERIC_RATIO = 0.7;
  const VERTICAL_GLYPH_ALLOWANCE_RATIO = 0.25;
  const MIN_CONTROL_GAP_PX = 8;
  const MAX_BAR_HEIGHT_PX = 96;
  const OFF_AXIS_MIN_PX = 1.5;
  const OFF_AXIS_MAX_PX = 8;
  const MAX_MARK_DEPTH = 4;
  const MIN_BAR_MARKS = 2;
  const MAX_DESCEND_CHILDREN = 1;
  const SINGLE_GRID_ROW = 1;
  const HALF_DIVISOR = 2;
  const PX_DECIMALS = 1;
  const NONE = 'none';
  const ZERO_OPACITY = '0';
  const HIDDEN_VISIBILITY = 'hidden';
  const CONTENTS_DISPLAY = 'contents';
  const INLINE_DISPLAY = 'inline';
  const FIXED_POSITION = 'fixed';
  const OVERFLOW_VISIBLE = 'visible';
  const CLIPPING_OVERFLOWS = ['hidden', 'clip'];
  const SCROLLING_OVERFLOWS = ['auto', 'scroll'];
  const ELLIPSIS = 'ellipsis';
  const POINTER_CURSOR = 'pointer';
  const TABULAR_NUMS = 'tabular-nums';
  const MS_UNIT = 'ms';
  const INFINITE = 'infinite';
  const TRUE_ATTRIBUTE = 'true';
  const DOCUMENT_LABEL = 'document';
  const LINEAR_TIMINGS = ['linear', 'cubic-bezier(0, 0, 1, 1)'];
  const LINEAR_SENSITIVE_PROPERTIES = ['transform', 'translate', 'top', 'left', 'width', 'height', 'all'];
  const BORDER_SIDES = ['Top', 'Right', 'Bottom', 'Left'];
  const HOVER_PSEUDO = ':hover';
  const ACTIVE_PSEUDO = ':active';
  const HOVER_REPLACEMENT = ':is(*)';
  const NESTING_SELECTOR = '&';
  const SELECTOR_SEPARATOR = ', ';
  const SELECTOR_JOINER = ' > ';
  const DETAIL_SEPARATOR = '; ';
  const DETAILS_TAG = 'DETAILS';
  const SUMMARY_TAG = 'SUMMARY';
  const INPUT_TAG = 'INPUT';
  const HTML_TAG = 'HTML';
  const BODY_TAG = 'BODY';
  const SVG_NAMESPACE = 'http://www.w3.org/2000/svg';
  const SKIPPED_TAGS = new Set(['HTML', 'HEAD', 'SCRIPT', 'STYLE', 'LINK', 'META', 'TITLE', 'NOSCRIPT', 'TEMPLATE', 'BR', 'WBR']);
  const LABELLED_INPUT_TYPES = new Set(['checkbox', 'radio']);
  const OPENING_BRACKETS = new Set(['(', '[']);
  const CLOSING_BRACKETS = new Set([')', ']']);
  const LIST_SEPARATOR = ',';
  const TARGET_SELECTOR = 'a[href], button, input, select, textarea, summary, [role="button"], [role="tab"], [role="link"], [role="menuitem"], [role="checkbox"], [role="switch"]';
  const TABINDEX_ATTRIBUTE = 'tabindex';
  const HOVER_CANDIDATE_SELECTOR = 'button, a[href], summary, [role="button"], [role="tab"], [role="menuitem"], [role="link"]';
  const DISABLED_SELECTOR = ':disabled';
  const ARIA_DISABLED_ATTRIBUTE = 'aria-disabled';
  const ARIA_LABEL_ATTRIBUTE = 'aria-label';
  const WHITESPACE_PATTERN = /\s+/g;
  const DIGIT_PATTERN = /\d/g;
  const NUMERIC_CHAR_PATTERN = /[\d.,%+\-−–:/'’$€£¥₹]/g;
  const MONOSPACE_PATTERN = /mono/i;
  const TNUM_ENABLED_PATTERN = /["']tnum["'](?!\s+(0|off))/;
  const TRANSPARENT_PATTERN = /^transparent$|,\s*0\)$|\/\s*0\)$/;
  const COMBINATOR_PATTERN = /[\s>+~]/;
  const HOVER_MEDIA_FEATURE_PATTERN = /\(\s*(any-)?(hover|pointer)\s*:\s*[a-z-]+\s*\)/gi;
  const MEDIA_ALWAYS_TRUE = '(min-width: 0px)';
  const TRANSLATE_FUNCTION_PATTERN = /translate[a-z0-9]*\(([^)]*)\)/gi;
  const NUMBER_PATTERN = /-?\d*\.?\d+/g;
  const LAYOUT_PROPERTY_PATTERN = /^(margin|padding|inset)(-.+)?$|^(top|left|right|bottom|width|height|font-weight)$|^border(-[a-z]+)*-width$/;
  const TRANSFORM_PROPERTY = 'transform';
  const TRANSLATE_PROPERTY = 'translate';
  const FLEX_DISPLAYS = ['flex', 'inline-flex'];
  const GRID_DISPLAYS = ['grid', 'inline-grid'];
  const ROW_DIRECTIONS = ['row', 'row-reverse'];
  const OUT_OF_FLOW_POSITIONS = ['absolute', 'fixed'];
  const BASELINE_ALIGNMENT = 'baseline';
  const JOINED_GROUP_ROLES = new Set(['tablist', 'radiogroup', 'group']);
  const ROLE_ATTRIBUTE = 'role';
  const IMG_TAG = 'IMG';
  const LINE_NAME_PATTERN = /\[[^\]]*\]/g;
  const ABOVE = 'above';
  const BELOW = 'below';
  const CATEGORY = {
    clippedText: 'clippedText',
    spilledText: 'spilledText',
    offscreen: 'offscreen',
    nestedScroll: 'nestedScroll',
    smallTargets: 'smallTargets',
    noHoverState: 'noHoverState',
    hoverMovesLayout: 'hoverMovesLayout',
    nonTabularNumbers: 'nonTabularNumbers',
    slowOrLinearMotion: 'slowOrLinearMotion',
    crampedSiblings: 'crampedSiblings',
    offAxis: 'offAxis',
  };
  const CATEGORIES = Object.values(CATEGORY);
  const NO_HOVER_DETAIL = 'no :hover rule matches';
  const SPACE = ' ';
  const SVG_ROOT_TAG = 'svg';
  const ALL_ELEMENTS_SELECTOR = '*';
  const HIDDEN_ATTRIBUTE = 'hidden';
  const DIRECT_SUMMARY_SELECTOR = ':scope > summary';
  const SIDE_LEFT = 'left';
  const SIDE_RIGHT = 'right';
  const SIDE_TOP = 'top';
  const SIDE_BOTTOM = 'bottom';

  const root = document.documentElement;
  const body = document.body;
  const styleCache = new Map();
  const counts = Object.fromEntries(CATEGORIES.map((category) => [category, 0]));
  const lists = Object.fromEntries(CATEGORIES.map((category) => [category, []]));
  const infiniteMotion = [];
  const renderedRects = new Map();
  const barContainers = [];

  const getStyle = (element) => {
    const cached = styleCache.get(element);
    if (cached) {
      return cached;
    }
    const style = getComputedStyle(element);
    styleCache.set(element, style);
    return style;
  };

  const record = (category, buildFinding) => {
    counts[category] += 1;
    if (lists[category].length < MAX_FINDINGS) {
      lists[category].push(buildFinding());
    }
  };

  const toRect = (rect) => ({
    x: Math.round(rect.x),
    y: Math.round(rect.y),
    width: Math.round(rect.width),
    height: Math.round(rect.height),
  });

  const collapseText = (text) => text.replace(WHITESPACE_PATTERN, SPACE).trim();

  const getOwnTextNodes = (element) => {
    const nodes = [];
    for (const node of element.childNodes) {
      if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {
        nodes.push(node);
      }
    }
    return nodes;
  };

  const joinText = (nodes) => collapseText(nodes.map((node) => node.textContent).join(SPACE));

  const describeText = (element, ownText) => {
    const label = ownText || element.getAttribute(ARIA_LABEL_ATTRIBUTE) || collapseText(element.textContent ?? '');
    return label.slice(0, MAX_TEXT_LENGTH);
  };

  const describePart = (element) => {
    const tag = element.tagName.toLowerCase();
    if (element.id) {
      return `${tag}#${CSS.escape(element.id)}`;
    }
    const classes = [...element.classList].slice(0, MAX_SELECTOR_CLASSES).map((name) => `.${CSS.escape(name)}`).join('');
    const parent = element.parentElement;
    if (classes || !parent) {
      return `${tag}${classes}`;
    }
    const sameTagSiblings = [...parent.children].filter((child) => child.tagName === element.tagName);
    if (sameTagSiblings.length === 1) {
      return tag;
    }
    return `${tag}:nth-of-type(${sameTagSiblings.indexOf(element) + 1})`;
  };

  const buildSelector = (element) => {
    const parts = [];
    let current = element;
    while (current && current !== root && current !== body && parts.length <= MAX_SELECTOR_ANCESTORS) {
      parts.unshift(describePart(current));
      if (current.id) {
        break;
      }
      current = current.parentElement;
    }
    if (parts.length === 0) {
      return element.tagName.toLowerCase();
    }
    return parts.join(SELECTOR_JOINER);
  };

  const elementFinding = (element, rect, ownText, detail, extra = {}) => ({
    selector: buildSelector(element),
    text: describeText(element, ownText),
    rect: toRect(rect),
    detail,
    ...extra,
  });

  const splitTopLevel = (text) => {
    const parts = [];
    let depth = 0;
    let current = '';
    for (const char of text) {
      if (OPENING_BRACKETS.has(char)) {
        depth += 1;
      }
      if (CLOSING_BRACKETS.has(char)) {
        depth -= 1;
      }
      if (char === LIST_SEPARATOR && depth === 0) {
        parts.push(current.trim());
        current = '';
        continue;
      }
      current += char;
    }
    parts.push(current.trim());
    return parts.filter(Boolean);
  };

  const mediaMatches = (mediaText) => {
    if (!mediaText) {
      return true;
    }
    try {
      if (matchMedia(mediaText).matches) {
        return true;
      }
      return matchMedia(mediaText.replace(HOVER_MEDIA_FEATURE_PATTERN, MEDIA_ALWAYS_TRUE)).matches;
    } catch {
      return false;
    }
  };

  const supportsMatches = (conditionText) => {
    try {
      return CSS.supports(conditionText);
    } catch {
      return false;
    }
  };

  const resolveNestedSelector = (selectorText, parentSelector) => {
    if (!parentSelector) {
      return selectorText;
    }
    const parentGroup = `:is(${parentSelector})`;
    return splitTopLevel(selectorText)
      .map((part) => {
        if (part.includes(NESTING_SELECTOR)) {
          return part.replaceAll(NESTING_SELECTOR, parentGroup);
        }
        return `${parentGroup} ${part}`;
      })
      .join(SELECTOR_SEPARATOR);
  };

  const collectStyleRules = () => {
    const rules = [];
    const visitedSheets = new Set();
    const visitRules = (ruleList, parentSelector) => {
      for (const rule of ruleList) {
        if (rule instanceof CSSMediaRule && !mediaMatches(rule.media.mediaText)) {
          continue;
        }
        if (rule instanceof CSSSupportsRule && !supportsMatches(rule.conditionText)) {
          continue;
        }
        if (rule instanceof CSSImportRule) {
          visitSheet(rule.styleSheet);
          continue;
        }
        if (rule instanceof CSSKeyframesRule) {
          continue;
        }
        if (rule instanceof CSSStyleRule) {
          const selector = resolveNestedSelector(rule.selectorText, parentSelector);
          rules.push({ selector, style: rule.style });
          if (rule.cssRules && rule.cssRules.length > 0) {
            visitRules(rule.cssRules, selector);
          }
          continue;
        }
        if (rule.cssRules) {
          visitRules(rule.cssRules, parentSelector);
        }
      }
    };
    const visitSheet = (sheet) => {
      if (!sheet || sheet.disabled || visitedSheets.has(sheet)) {
        return;
      }
      visitedSheets.add(sheet);
      if (sheet.media && !mediaMatches(sheet.media.mediaText)) {
        return;
      }
      let ruleList = null;
      try {
        ruleList = sheet.cssRules;
      } catch {
        return;
      }
      if (ruleList) {
        visitRules(ruleList, '');
      }
    };
    for (const sheet of document.styleSheets) {
      visitSheet(sheet);
    }
    for (const sheet of document.adoptedStyleSheets ?? []) {
      visitSheet(sheet);
    }
    return rules;
  };

  const hoverIsOnSubject = (selector) => {
    const index = selector.lastIndexOf(HOVER_PSEUDO);
    let depth = 0;
    for (const char of selector.slice(index + HOVER_PSEUDO.length)) {
      if (OPENING_BRACKETS.has(char)) {
        depth += 1;
      }
      if (CLOSING_BRACKETS.has(char)) {
        depth -= 1;
      }
      if (depth <= 0 && COMBINATOR_PATTERN.test(char)) {
        return false;
      }
    }
    return true;
  };

  const buildHoverCoverage = (rules) => {
    const covered = new Set();
    const ancestorsMarked = new Set();
    const markAncestors = (element) => {
      let ancestor = element.parentElement;
      while (ancestor && !ancestorsMarked.has(ancestor)) {
        ancestorsMarked.add(ancestor);
        covered.add(ancestor);
        ancestor = ancestor.parentElement;
      }
    };
    for (const rule of rules) {
      if (!rule.selector.includes(HOVER_PSEUDO) || rule.style.length === 0) {
        continue;
      }
      for (const part of splitTopLevel(rule.selector)) {
        if (!part.includes(HOVER_PSEUDO)) {
          continue;
        }
        let matched = [];
        try {
          matched = document.querySelectorAll(part.replaceAll(HOVER_PSEUDO, HOVER_REPLACEMENT));
        } catch {
          continue;
        }
        const includeAncestors = !hoverIsOnSubject(part);
        for (const element of matched) {
          covered.add(element);
          if (includeAncestors) {
            markAncestors(element);
          }
        }
      }
    }
    return covered;
  };

  const hasNonZeroNumber = (text) => (text.match(NUMBER_PATTERN) ?? []).some((value) => Number.parseFloat(value) !== 0);

  const hasTranslation = (value) => {
    for (const match of value.matchAll(TRANSLATE_FUNCTION_PATTERN)) {
      if (hasNonZeroNumber(match[1])) {
        return true;
      }
    }
    return false;
  };

  const findLayoutDeclarations = (style) => {
    const offending = [];
    for (const property of style) {
      const value = style.getPropertyValue(property);
      if (property === TRANSFORM_PROPERTY && hasTranslation(value)) {
        offending.push(`${property}: ${value}`);
        continue;
      }
      if (property === TRANSLATE_PROPERTY && value !== NONE && hasNonZeroNumber(value)) {
        offending.push(`${property}: ${value}`);
        continue;
      }
      if (LAYOUT_PROPERTY_PATTERN.test(property)) {
        offending.push(`${property}: ${value}`);
      }
    }
    return offending;
  };

  const auditInteractionRules = (rules) => {
    const seen = new Set();
    for (const rule of rules) {
      if (!rule.selector.includes(HOVER_PSEUDO) && !rule.selector.includes(ACTIVE_PSEUDO)) {
        continue;
      }
      const offending = findLayoutDeclarations(rule.style);
      if (offending.length === 0) {
        continue;
      }
      const detail = offending.join(DETAIL_SEPARATOR);
      const key = `${rule.selector}|${detail}`;
      if (seen.has(key)) {
        continue;
      }
      seen.add(key);
      record(CATEGORY.hoverMovesLayout, () => ({ selector: rule.selector, detail }));
    }
  };

  const isTransparent = (color) => TRANSPARENT_PATTERN.test(color);

  const hasRadius = (style) => [style.borderTopLeftRadius, style.borderTopRightRadius, style.borderBottomRightRadius, style.borderBottomLeftRadius]
    .some((radius) => Number.parseFloat(radius) > 0);

  const hasBorder = (style) => BORDER_SIDES.some((side) => Number.parseFloat(style[`border${side}Width`]) > 0 && style[`border${side}Style`] !== NONE);

  const hasVisibleBox = (style) => {
    if (!isTransparent(style.backgroundColor) || style.backgroundImage !== NONE) {
      return true;
    }
    if (style.overflowX !== OVERFLOW_VISIBLE || style.overflowY !== OVERFLOW_VISIBLE) {
      return true;
    }
    return hasBorder(style) || hasRadius(style);
  };

  const measureTextBounds = (textNodes) => {
    const range = document.createRange();
    let bounds = null;
    for (const node of textNodes) {
      range.selectNodeContents(node);
      const rect = range.getBoundingClientRect();
      if (rect.width === 0 && rect.height === 0) {
        continue;
      }
      if (!bounds) {
        bounds = { left: rect.left, top: rect.top, right: rect.right, bottom: rect.bottom };
        continue;
      }
      bounds.left = Math.min(bounds.left, rect.left);
      bounds.top = Math.min(bounds.top, rect.top);
      bounds.right = Math.max(bounds.right, rect.right);
      bounds.bottom = Math.max(bounds.bottom, rect.bottom);
    }
    return bounds;
  };

  const describeOvershoot = (text, box, verticalAllowance) => {
    const overshoots = [
      [SIDE_LEFT, box.left - text.left, 0],
      [SIDE_RIGHT, text.right - box.right, 0],
      [SIDE_TOP, box.top - text.top, verticalAllowance],
      [SIDE_BOTTOM, text.bottom - box.bottom, verticalAllowance],
    ];
    return overshoots
      .filter(([, amount, allowance]) => amount - allowance > TOLERANCE_PX)
      .map(([side, amount]) => `${side} +${Math.round(amount)}px`)
      .join(SPACE);
  };

  const auditSpill = (element, style, rect, textNodes, ownText, parentState) => {
    const bounds = measureTextBounds(textNodes);
    if (!bounds) {
      return;
    }
    const verticalAllowance = Number.parseFloat(style.fontSize) * VERTICAL_GLYPH_ALLOWANCE_RATIO;
    const ownOvershoot = describeOvershoot(bounds, rect, verticalAllowance);
    if (ownOvershoot) {
      record(CATEGORY.spilledText, () => elementFinding(element, rect, ownText, `text past own box: ${ownOvershoot}`));
      return;
    }
    const box = parentState.nearestBox;
    if (!box || box.scrolls) {
      return;
    }
    const boxOvershoot = describeOvershoot(bounds, box.rect, verticalAllowance);
    if (boxOvershoot) {
      record(CATEGORY.spilledText, () => elementFinding(element, rect, ownText, `text past ${buildSelector(box.element)}: ${boxOvershoot}`));
    }
  };

  const auditClip = (element, style, rect, ownText) => {
    if (style.textOverflow === ELLIPSIS || (style.webkitLineClamp && style.webkitLineClamp !== NONE)) {
      return;
    }
    const details = [];
    if (CLIPPING_OVERFLOWS.includes(style.overflowX) && element.scrollWidth > element.clientWidth + TOLERANCE_PX) {
      details.push(`scrollWidth ${element.scrollWidth} > clientWidth ${element.clientWidth}`);
    }
    if (CLIPPING_OVERFLOWS.includes(style.overflowY) && element.scrollHeight > element.clientHeight + TOLERANCE_PX) {
      details.push(`scrollHeight ${element.scrollHeight} > clientHeight ${element.clientHeight}`);
    }
    if (details.length > 0) {
      record(CATEGORY.clippedText, () => elementFinding(element, rect, ownText, details.join(DETAIL_SEPARATOR)));
    }
  };

  const isInRunningText = (element, style) => {
    if (style.display !== INLINE_DISPLAY || !element.parentElement) {
      return false;
    }
    return getOwnTextNodes(element.parentElement).length > 0;
  };

  const hasLargeLabel = (element) => {
    if (element.tagName !== INPUT_TAG || !LABELLED_INPUT_TYPES.has(element.type) || !element.labels) {
      return false;
    }
    return [...element.labels].some((label) => {
      const labelRect = label.getBoundingClientRect();
      return labelRect.width >= MIN_TARGET_PX && labelRect.height >= MIN_TARGET_PX;
    });
  };

  const isTarget = (element) => {
    if (element.matches(TARGET_SELECTOR)) {
      return true;
    }
    return element.hasAttribute(TABINDEX_ATTRIBUTE) && element.tabIndex >= 0;
  };

  const auditTarget = (element, style, rect, ownText) => {
    if (rect.width >= MIN_TARGET_PX && rect.height >= MIN_TARGET_PX) {
      return;
    }
    if (isInRunningText(element, style) || hasLargeLabel(element)) {
      return;
    }
    record(CATEGORY.smallTargets, () => elementFinding(element, rect, ownText, `${Number(rect.width.toFixed(2))}x${Number(rect.height.toFixed(2))} < ${MIN_TARGET_PX}x${MIN_TARGET_PX}`));
  };

  const isDisabled = (element) => element.matches(DISABLED_SELECTOR) || element.getAttribute(ARIA_DISABLED_ATTRIBUTE) === TRUE_ATTRIBUTE;

  const isHoverCandidate = (element, style, parentState) => {
    if (element.matches(HOVER_CANDIDATE_SELECTOR)) {
      return true;
    }
    return style.cursor === POINTER_CURSOR && parentState.cursor !== POINTER_CURSOR;
  };

  const isPredominantlyNumeric = (text) => {
    const compact = text.replace(WHITESPACE_PATTERN, '');
    const digitCount = (compact.match(DIGIT_PATTERN) ?? []).length;
    if (digitCount < MIN_NUMERIC_DIGITS) {
      return false;
    }
    const numericCount = (compact.match(NUMERIC_CHAR_PATTERN) ?? []).length;
    return numericCount / compact.length >= NUMERIC_RATIO;
  };

  const hasTabularFigures = (style) => {
    if (style.fontVariantNumeric.includes(TABULAR_NUMS)) {
      return true;
    }
    if (TNUM_ENABLED_PATTERN.test(style.fontFeatureSettings)) {
      return true;
    }
    return MONOSPACE_PATTERN.test(style.fontFamily);
  };

  const parseDurations = (value) => value.split(LIST_SEPARATOR).map((part) => {
    const trimmed = part.trim();
    const amount = Number.parseFloat(trimmed);
    if (Number.isNaN(amount)) {
      return 0;
    }
    if (trimmed.endsWith(MS_UNIT)) {
      return amount;
    }
    return amount * MS_PER_SECOND;
  });

  const pickCyclic = (list, index) => list[index % list.length];

  const collectTransitionIssues = (style) => {
    const issues = [];
    const properties = splitTopLevel(style.transitionProperty);
    const durations = parseDurations(style.transitionDuration);
    const timings = splitTopLevel(style.transitionTimingFunction);
    properties.forEach((property, index) => {
      const duration = pickCyclic(durations, index);
      const timing = pickCyclic(timings, index);
      if (!duration || property === NONE) {
        return;
      }
      if (duration > SLOW_MOTION_MS) {
        issues.push(`transition ${property} ${Math.round(duration)}ms > ${SLOW_MOTION_MS}ms`);
      }
      if (LINEAR_TIMINGS.includes(timing) && LINEAR_SENSITIVE_PROPERTIES.includes(property)) {
        issues.push(`linear transition on ${property}`);
      }
    });
    return issues;
  };

  const collectAnimationIssues = (style) => {
    const finite = [];
    const infinite = [];
    const names = splitTopLevel(style.animationName);
    const durations = parseDurations(style.animationDuration);
    const iterations = splitTopLevel(style.animationIterationCount);
    names.forEach((name, index) => {
      const duration = pickCyclic(durations, index);
      if (name === NONE || duration <= SLOW_MOTION_MS) {
        return;
      }
      const issue = `animation ${name} ${Math.round(duration)}ms > ${SLOW_MOTION_MS}ms`;
      if (pickCyclic(iterations, index) === INFINITE) {
        infinite.push(issue);
        return;
      }
      finite.push(issue);
    });
    return { finite, infinite };
  };

  const auditMotion = (element, rect, ownText, style) => {
    const transitionIssues = collectTransitionIssues(style);
    const animationIssues = collectAnimationIssues(style);
    const finiteIssues = [...transitionIssues, ...animationIssues.finite];
    if (finiteIssues.length > 0) {
      record(CATEGORY.slowOrLinearMotion, () => elementFinding(element, rect, ownText, finiteIssues.join(DETAIL_SEPARATOR), { infinite: false }));
      return;
    }
    if (animationIssues.infinite.length === 0) {
      return;
    }
    counts.slowOrLinearMotion += 1;
    if (infiniteMotion.length < MAX_FINDINGS) {
      infiniteMotion.push(elementFinding(element, rect, ownText, animationIssues.infinite.join(DETAIL_SEPARATOR), { infinite: true }));
    }
  };

  const isClosedDetailsContent = (element) => {
    const parent = element.parentElement;
    if (!parent || parent.tagName !== DETAILS_TAG || parent.open) {
      return false;
    }
    if (element.tagName !== SUMMARY_TAG) {
      return true;
    }
    return parent.querySelector(DIRECT_SUMMARY_SELECTOR) !== element;
  };

  const isDocumentRoot = (element) => element.tagName === HTML_TAG || element.tagName === BODY_TAG;

  const isScrollingX = (element, style) => !isDocumentRoot(element)
    && SCROLLING_OVERFLOWS.includes(style.overflowX)
    && element.scrollWidth > element.clientWidth + TOLERANCE_PX;

  const isScrollingY = (element, style) => !isDocumentRoot(element)
    && SCROLLING_OVERFLOWS.includes(style.overflowY)
    && element.scrollHeight > element.clientHeight + TOLERANCE_PX;

  const describeScroller = (scroller) => {
    if (scroller === DOCUMENT_LABEL) {
      return DOCUMENT_LABEL;
    }
    return buildSelector(scroller);
  };

  const auditScroll = (element, rect, ownText, scrollsX, scrollsY, parentState) => {
    if (scrollsX && scrollsY) {
      record(CATEGORY.nestedScroll, () => elementFinding(element, rect, ownText, `scrolls on both axes: ${element.scrollWidth}x${element.scrollHeight} in ${element.clientWidth}x${element.clientHeight}`));
      return;
    }
    if (scrollsX && parentState.scrollerX) {
      record(CATEGORY.nestedScroll, () => elementFinding(element, rect, ownText, `horizontal scroller inside horizontal scroller ${describeScroller(parentState.scrollerX)}`));
      return;
    }
    if (scrollsY && parentState.scrollerY) {
      record(CATEGORY.nestedScroll, () => elementFinding(element, rect, ownText, `vertical scroller inside vertical scroller ${describeScroller(parentState.scrollerY)}`));
    }
  };

  const formatPx = (value) => Number(value.toFixed(PX_DECIMALS));

  const hasFillOrBorder = (style) => !isTransparent(style.backgroundColor) || style.backgroundImage !== NONE || hasBorder(style);

  const hasPaintedBox = (style) => hasFillOrBorder(style) || style.boxShadow !== NONE;

  const isJoinedGroup = (parent) => {
    if (JOINED_GROUP_ROLES.has(parent.getAttribute(ROLE_ATTRIBUTE))) {
      return true;
    }
    const style = getStyle(parent);
    if (GRID_DISPLAYS.includes(style.display) && countGridRows(style) > SINGLE_GRID_ROW) {
      return true;
    }
    const clips =CLIPPING_OVERFLOWS.includes(style.overflowX) || CLIPPING_OVERFLOWS.includes(style.overflowY);
    return clips && hasRadius(style) && hasFillOrBorder(style);
  };

  const isPaintedControl = (element) => renderedRects.has(element) && isTarget(element) && hasPaintedBox(getStyle(element));

  const findNextRenderedSibling = (element) => {
    let sibling = element.nextElementSibling;
    while (sibling && !renderedRects.has(sibling)) {
      sibling = sibling.nextElementSibling;
    }
    return sibling;
  };

  const measureOverlap = (startA, endA, startB, endB) => Math.min(endA, endB) - Math.max(startA, startB);

  const measureGap = (first, second) => {
    if (measureOverlap(first.top, first.bottom, second.top, second.bottom) > 0) {
      return Math.max(second.left - first.right, first.left - second.right);
    }
    if (measureOverlap(first.left, first.right, second.left, second.right) > 0) {
      return Math.max(second.top - first.bottom, first.top - second.bottom);
    }
    return null;
  };

  const auditCrampedSiblings = () => {
    for (const [element, rect] of renderedRects) {
      const parent = element.parentElement;
      if (!parent || !isPaintedControl(element)) {
        continue;
      }
      const sibling = findNextRenderedSibling(element);
      if (!sibling || !isPaintedControl(sibling) || isJoinedGroup(parent)) {
        continue;
      }
      const gap = measureGap(rect, renderedRects.get(sibling));
      if (gap === null || gap < TOLERANCE_PX || gap >= MIN_CONTROL_GAP_PX) {
        continue;
      }
      record(CATEGORY.crampedSiblings, () => elementFinding(element, rect, joinText(getOwnTextNodes(element)), `gap ${formatPx(gap)}px < ${MIN_CONTROL_GAP_PX}px to ${buildSelector(sibling)}`));
    }
  };

  const countGridRows = (style) => {
    const tracks = style.gridTemplateRows.replace(LINE_NAME_PATTERN, SPACE).trim();
    if (!tracks || tracks === NONE) {
      return 0;
    }
    return tracks.split(WHITESPACE_PATTERN).length;
  };

  const isRowLayout = (style) => {
    if (FLEX_DISPLAYS.includes(style.display)) {
      return ROW_DIRECTIONS.includes(style.flexDirection);
    }
    if (GRID_DISPLAYS.includes(style.display)) {
      return countGridRows(style) === SINGLE_GRID_ROW;
    }
    return false;
  };

  const isStackingLayout = (style) => {
    if (FLEX_DISPLAYS.includes(style.display)) {
      return !ROW_DIRECTIONS.includes(style.flexDirection);
    }
    if (GRID_DISPLAYS.includes(style.display)) {
      return countGridRows(style) > SINGLE_GRID_ROW;
    }
    return false;
  };

  const isGraphic = (element) => element.tagName === IMG_TAG || (element.namespaceURI === SVG_NAMESPACE && element.tagName.toLowerCase() === SVG_ROOT_TAG);

  const countRenderedChildren = (element) => [...element.children].filter((child) => renderedRects.has(child)).length;

  const findWrappedGraphic = (element) => {
    let current = element;
    while (current && renderedRects.has(current) && !isGraphic(current)) {
      if (current.namespaceURI === SVG_NAMESPACE || getOwnTextNodes(current).length > 0 || OUT_OF_FLOW_POSITIONS.includes(getStyle(current).position)) {
        return null;
      }
      const renderedChildren = [...current.children].filter((child) => renderedRects.has(child));
      if (renderedChildren.length !== MAX_DESCEND_CHILDREN) {
        return null;
      }
      current = renderedChildren[0];
    }
    if (current && renderedRects.has(current)) {
      return current;
    }
    return null;
  };

  const canDescend = (element, style) => {
    if (isRowLayout(style)) {
      return true;
    }
    if (isStackingLayout(style)) {
      return false;
    }
    return countRenderedChildren(element) <= MAX_DESCEND_CHILDREN;
  };

  const collectMarks = (container) => {
    const marks = [];
    const visit = (element, depth, baselineAligned) => {
      const rect = renderedRects.get(element);
      if (!rect) {
        return;
      }
      const style = getStyle(element);
      if (depth > 0 && OUT_OF_FLOW_POSITIONS.includes(style.position)) {
        return;
      }
      const aligned = baselineAligned || style.alignSelf.includes(BASELINE_ALIGNMENT);
      if (isGraphic(element)) {
        if (!aligned && rect.width >= MIN_VISIBLE_SIZE_PX && rect.height >= MIN_VISIBLE_SIZE_PX) {
          marks.push({ element, rect, text: '', graphic: true });
        }
        return;
      }
      if (element.namespaceURI === SVG_NAMESPACE) {
        return;
      }
      const textNodes = getOwnTextNodes(element);
      const bounds = measureTextBounds(textNodes);
      if (bounds && !aligned) {
        marks.push({
          element,
          rect: new DOMRect(bounds.left, bounds.top, bounds.right - bounds.left, bounds.bottom - bounds.top),
          text: joinText(textNodes),
          graphic: false,
        });
      }
      if (depth >= MAX_MARK_DEPTH) {
        return;
      }
      const childrenAligned = style.alignItems.includes(BASELINE_ALIGNMENT);
      const rowLayout = isRowLayout(style);
      if (bounds && !rowLayout) {
        for (const child of element.children) {
          const graphic = findWrappedGraphic(child);
          if (graphic) {
            visit(graphic, depth + 1, childrenAligned);
          }
        }
        return;
      }
      if (depth > 0 && !canDescend(element, style)) {
        return;
      }
      for (const child of element.children) {
        visit(child, depth + 1, childrenAligned);
      }
    };
    visit(container, 0, false);
    return marks;
  };

  const computeMedian = (values) => {
    const sorted = [...values].sort((first, second) => first - second);
    const middle = Math.floor(sorted.length / HALF_DIVISOR);
    if (sorted.length % HALF_DIVISOR === 0) {
      return (sorted[middle - 1] + sorted[middle]) / HALF_DIVISOR;
    }
    return sorted[middle];
  };

  const auditOffAxis = () => {
    const evaluated = new Set();
    for (const container of barContainers) {
      const allMarks = collectMarks(container);
      const marks = allMarks.filter((mark) => !evaluated.has(mark.element));
      if (marks.length < MIN_BAR_MARKS || !allMarks.some((mark) => mark.graphic)) {
        continue;
      }
      for (const mark of marks) {
        evaluated.add(mark.element);
      }
      const centres = marks.map((mark) => (mark.rect.top + mark.rect.bottom) / HALF_DIVISOR);
      const axis = computeMedian(centres);
      marks.forEach((mark, index) => {
        const offset = centres[index] - axis;
        const distance = Math.abs(offset);
        if (distance <= OFF_AXIS_MIN_PX || distance >= OFF_AXIS_MAX_PX) {
          return;
        }
        if (mark.rect.top > axis || mark.rect.bottom < axis) {
          return;
        }
        const side = offset < 0 ? ABOVE : BELOW;
        record(CATEGORY.offAxis, () => elementFinding(mark.element, mark.rect, mark.text, `centre ${formatPx(distance)}px ${side} the bar axis of ${buildSelector(container)}`));
      });
    }
  };

  const rootStyle = getStyle(root);
  const bodyStyle = body ? getStyle(body) : rootStyle;
  const scrollingElement = document.scrollingElement ?? root;
  const pageClipsX = CLIPPING_OVERFLOWS.includes(rootStyle.overflowX) || CLIPPING_OVERFLOWS.includes(bodyStyle.overflowX);
  const pageClipsY = CLIPPING_OVERFLOWS.includes(rootStyle.overflowY) || CLIPPING_OVERFLOWS.includes(bodyStyle.overflowY);
  const pageScroll = {
    horizontal: !pageClipsX && scrollingElement.scrollWidth > scrollingElement.clientWidth + TOLERANCE_PX,
    vertical: !pageClipsY && scrollingElement.scrollHeight > scrollingElement.clientHeight + TOLERANCE_PX,
    scrollWidth: Math.round(scrollingElement.scrollWidth),
    scrollHeight: Math.round(scrollingElement.scrollHeight),
  };
  const viewportWidth = root.clientWidth;

  const rules = collectStyleRules();
  const hoverCoverage = buildHoverCoverage(rules);
  auditInteractionRules(rules);

  const rootState = {
    subtreeHidden: false,
    insideClipX: false,
    insideOffscreen: false,
    nearestBox: null,
    scrollerX: pageScroll.horizontal ? DOCUMENT_LABEL : null,
    scrollerY: pageScroll.vertical ? DOCUMENT_LABEL : null,
    cursor: '',
  };
  const stateByElement = new Map();

  for (const element of document.querySelectorAll(ALL_ELEMENTS_SELECTOR)) {
    const parentState = stateByElement.get(element.parentElement) ?? rootState;
    const style = getStyle(element);
    const subtreeHidden = parentState.subtreeHidden
      || element.hasAttribute(HIDDEN_ATTRIBUTE)
      || style.display === NONE
      || style.opacity === ZERO_OPACITY
      || isClosedDetailsContent(element);
    const state = { ...parentState, subtreeHidden, cursor: style.cursor };
    stateByElement.set(element, state);
    if (subtreeHidden || SKIPPED_TAGS.has(element.tagName)) {
      continue;
    }
    const rect = element.getBoundingClientRect();
    const isSvgChild = element.namespaceURI === SVG_NAMESPACE && element.tagName.toLowerCase() !== SVG_ROOT_TAG;
    const scrollsX = !isSvgChild && isScrollingX(element, style);
    const scrollsY = !isSvgChild && isScrollingY(element, style);
    if (scrollsX) {
      state.scrollerX = element;
    }
    if (scrollsY) {
      state.scrollerY = element;
    }
    if (style.overflowX !== OVERFLOW_VISIBLE) {
      state.insideClipX = true;
    }
    if (style.position === FIXED_POSITION) {
      state.nearestBox = null;
    }
    if (element !== body && hasVisibleBox(style)) {
      state.nearestBox = {
        element,
        rect,
        scrolls: SCROLLING_OVERFLOWS.includes(style.overflowX) || SCROLLING_OVERFLOWS.includes(style.overflowY),
      };
    }
    const rendered = style.visibility !== HIDDEN_VISIBILITY
      && style.display !== CONTENTS_DISPLAY
      && rect.width > 0
      && rect.height > 0;
    if (!rendered) {
      continue;
    }
    renderedRects.set(element, rect);
    if (!isSvgChild && rect.height < MAX_BAR_HEIGHT_PX && isRowLayout(style)) {
      barContainers.push(element);
    }
    const textNodes = getOwnTextNodes(element);
    const ownText = joinText(textNodes);
    if (ownText) {
      auditClip(element, style, rect, ownText);
      if (style.overflowX === OVERFLOW_VISIBLE && style.overflowY === OVERFLOW_VISIBLE) {
        auditSpill(element, style, rect, textNodes, ownText, parentState);
      }
      if (isPredominantlyNumeric(ownText) && !hasTabularFigures(style)) {
        record(CATEGORY.nonTabularNumbers, () => elementFinding(element, rect, ownText, `font-variant-numeric: ${style.fontVariantNumeric}`));
      }
    }
    const left = rect.left + window.scrollX;
    const right = rect.right + window.scrollX;
    const isVisibleSize = rect.width >= MIN_VISIBLE_SIZE_PX && rect.height >= MIN_VISIBLE_SIZE_PX;
    if (!parentState.insideClipX && !parentState.insideOffscreen && isVisibleSize && (left < -TOLERANCE_PX || right > viewportWidth + TOLERANCE_PX)) {
      state.insideOffscreen = true;
      record(CATEGORY.offscreen, () => elementFinding(element, rect, ownText, `spans ${Math.round(left)}..${Math.round(right)} outside viewport 0..${viewportWidth}`));
    }
    auditScroll(element, rect, ownText, scrollsX, scrollsY, parentState);
    if (isTarget(element)) {
      auditTarget(element, style, rect, ownText);
    }
    if (isHoverCandidate(element, style, parentState) && !isDisabled(element) && !hoverCoverage.has(element)) {
      record(CATEGORY.noHoverState, () => elementFinding(element, rect, ownText, NO_HOVER_DETAIL));
    }
    auditMotion(element, rect, ownText, style);
  }
  auditCrampedSiblings();
  auditOffAxis();

  return {
    viewport: { width: window.innerWidth, height: window.innerHeight },
    pageScroll,
    counts,
    clippedText: lists.clippedText,
    spilledText: lists.spilledText,
    offscreen: lists.offscreen,
    nestedScroll: lists.nestedScroll,
    smallTargets: lists.smallTargets,
    noHoverState: lists.noHoverState,
    hoverMovesLayout: lists.hoverMovesLayout,
    nonTabularNumbers: lists.nonTabularNumbers,
    slowOrLinearMotion: [...lists.slowOrLinearMotion, ...infiniteMotion].slice(0, MAX_FINDINGS),
    crampedSiblings: lists.crampedSiblings,
    offAxis: lists.offAxis,
  };
}
