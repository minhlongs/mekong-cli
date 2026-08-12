// packages/ui/src/components/button.tsx
import * as React from "react";

// node_modules/.pnpm/clsx@2.1.1/node_modules/clsx/dist/clsx.mjs
function r(e) {
  var t, f, n = "";
  if ("string" == typeof e || "number" == typeof e) n += e;
  else if ("object" == typeof e) if (Array.isArray(e)) {
    var o = e.length;
    for (t = 0; t < o; t++) e[t] && (f = r(e[t])) && (n && (n += " "), n += f);
  } else for (f in e) e[f] && (n && (n += " "), n += f);
  return n;
}
function clsx() {
  for (var e, t, f = 0, n = "", o = arguments.length; f < o; f++) (e = arguments[f]) && (t = r(e)) && (n && (n += " "), n += t);
  return n;
}

// node_modules/.pnpm/class-variance-authority@0.7.1/node_modules/class-variance-authority/dist/index.mjs
var falsyToString = (value) => typeof value === "boolean" ? `${value}` : value === 0 ? "0" : value;
var cx = clsx;
var cva = (base, config) => (props) => {
  var _config_compoundVariants;
  if ((config === null || config === void 0 ? void 0 : config.variants) == null) return cx(base, props === null || props === void 0 ? void 0 : props.class, props === null || props === void 0 ? void 0 : props.className);
  const { variants, defaultVariants } = config;
  const getVariantClassNames = Object.keys(variants).map((variant) => {
    const variantProp = props === null || props === void 0 ? void 0 : props[variant];
    const defaultVariantProp = defaultVariants === null || defaultVariants === void 0 ? void 0 : defaultVariants[variant];
    if (variantProp === null) return null;
    const variantKey = falsyToString(variantProp) || falsyToString(defaultVariantProp);
    return variants[variant][variantKey];
  });
  const propsWithoutUndefined = props && Object.entries(props).reduce((acc, param) => {
    let [key, value] = param;
    if (value === void 0) {
      return acc;
    }
    acc[key] = value;
    return acc;
  }, {});
  const getCompoundVariantClassNames = config === null || config === void 0 ? void 0 : (_config_compoundVariants = config.compoundVariants) === null || _config_compoundVariants === void 0 ? void 0 : _config_compoundVariants.reduce((acc, param) => {
    let { class: cvClass, className: cvClassName, ...compoundVariantOptions } = param;
    return Object.entries(compoundVariantOptions).every((param2) => {
      let [key, value] = param2;
      return Array.isArray(value) ? value.includes({
        ...defaultVariants,
        ...propsWithoutUndefined
      }[key]) : {
        ...defaultVariants,
        ...propsWithoutUndefined
      }[key] === value;
    }) ? [
      ...acc,
      cvClass,
      cvClassName
    ] : acc;
  }, []);
  return cx(base, getVariantClassNames, getCompoundVariantClassNames, props === null || props === void 0 ? void 0 : props.class, props === null || props === void 0 ? void 0 : props.className);
};

// node_modules/.pnpm/tailwind-merge@3.5.0/node_modules/tailwind-merge/dist/bundle-mjs.mjs
var concatArrays = (array1, array2) => {
  const combinedArray = new Array(array1.length + array2.length);
  for (let i = 0; i < array1.length; i++) {
    combinedArray[i] = array1[i];
  }
  for (let i = 0; i < array2.length; i++) {
    combinedArray[array1.length + i] = array2[i];
  }
  return combinedArray;
};
var createClassValidatorObject = (classGroupId, validator) => ({
  classGroupId,
  validator
});
var createClassPartObject = (nextPart = /* @__PURE__ */ new Map(), validators = null, classGroupId) => ({
  nextPart,
  validators,
  classGroupId
});
var CLASS_PART_SEPARATOR = "-";
var EMPTY_CONFLICTS = [];
var ARBITRARY_PROPERTY_PREFIX = "arbitrary..";
var createClassGroupUtils = (config) => {
  const classMap = createClassMap(config);
  const {
    conflictingClassGroups,
    conflictingClassGroupModifiers
  } = config;
  const getClassGroupId = (className) => {
    if (className.startsWith("[") && className.endsWith("]")) {
      return getGroupIdForArbitraryProperty(className);
    }
    const classParts = className.split(CLASS_PART_SEPARATOR);
    const startIndex = classParts[0] === "" && classParts.length > 1 ? 1 : 0;
    return getGroupRecursive(classParts, startIndex, classMap);
  };
  const getConflictingClassGroupIds = (classGroupId, hasPostfixModifier) => {
    if (hasPostfixModifier) {
      const modifierConflicts = conflictingClassGroupModifiers[classGroupId];
      const baseConflicts = conflictingClassGroups[classGroupId];
      if (modifierConflicts) {
        if (baseConflicts) {
          return concatArrays(baseConflicts, modifierConflicts);
        }
        return modifierConflicts;
      }
      return baseConflicts || EMPTY_CONFLICTS;
    }
    return conflictingClassGroups[classGroupId] || EMPTY_CONFLICTS;
  };
  return {
    getClassGroupId,
    getConflictingClassGroupIds
  };
};
var getGroupRecursive = (classParts, startIndex, classPartObject) => {
  const classPathsLength = classParts.length - startIndex;
  if (classPathsLength === 0) {
    return classPartObject.classGroupId;
  }
  const currentClassPart = classParts[startIndex];
  const nextClassPartObject = classPartObject.nextPart.get(currentClassPart);
  if (nextClassPartObject) {
    const result = getGroupRecursive(classParts, startIndex + 1, nextClassPartObject);
    if (result) return result;
  }
  const validators = classPartObject.validators;
  if (validators === null) {
    return void 0;
  }
  const classRest = startIndex === 0 ? classParts.join(CLASS_PART_SEPARATOR) : classParts.slice(startIndex).join(CLASS_PART_SEPARATOR);
  const validatorsLength = validators.length;
  for (let i = 0; i < validatorsLength; i++) {
    const validatorObj = validators[i];
    if (validatorObj.validator(classRest)) {
      return validatorObj.classGroupId;
    }
  }
  return void 0;
};
var getGroupIdForArbitraryProperty = (className) => className.slice(1, -1).indexOf(":") === -1 ? void 0 : (() => {
  const content = className.slice(1, -1);
  const colonIndex = content.indexOf(":");
  const property = content.slice(0, colonIndex);
  return property ? ARBITRARY_PROPERTY_PREFIX + property : void 0;
})();
var createClassMap = (config) => {
  const {
    theme,
    classGroups
  } = config;
  return processClassGroups(classGroups, theme);
};
var processClassGroups = (classGroups, theme) => {
  const classMap = createClassPartObject();
  for (const classGroupId in classGroups) {
    const group = classGroups[classGroupId];
    processClassesRecursively(group, classMap, classGroupId, theme);
  }
  return classMap;
};
var processClassesRecursively = (classGroup, classPartObject, classGroupId, theme) => {
  const len = classGroup.length;
  for (let i = 0; i < len; i++) {
    const classDefinition = classGroup[i];
    processClassDefinition(classDefinition, classPartObject, classGroupId, theme);
  }
};
var processClassDefinition = (classDefinition, classPartObject, classGroupId, theme) => {
  if (typeof classDefinition === "string") {
    processStringDefinition(classDefinition, classPartObject, classGroupId);
    return;
  }
  if (typeof classDefinition === "function") {
    processFunctionDefinition(classDefinition, classPartObject, classGroupId, theme);
    return;
  }
  processObjectDefinition(classDefinition, classPartObject, classGroupId, theme);
};
var processStringDefinition = (classDefinition, classPartObject, classGroupId) => {
  const classPartObjectToEdit = classDefinition === "" ? classPartObject : getPart(classPartObject, classDefinition);
  classPartObjectToEdit.classGroupId = classGroupId;
};
var processFunctionDefinition = (classDefinition, classPartObject, classGroupId, theme) => {
  if (isThemeGetter(classDefinition)) {
    processClassesRecursively(classDefinition(theme), classPartObject, classGroupId, theme);
    return;
  }
  if (classPartObject.validators === null) {
    classPartObject.validators = [];
  }
  classPartObject.validators.push(createClassValidatorObject(classGroupId, classDefinition));
};
var processObjectDefinition = (classDefinition, classPartObject, classGroupId, theme) => {
  const entries = Object.entries(classDefinition);
  const len = entries.length;
  for (let i = 0; i < len; i++) {
    const [key, value] = entries[i];
    processClassesRecursively(value, getPart(classPartObject, key), classGroupId, theme);
  }
};
var getPart = (classPartObject, path) => {
  let current = classPartObject;
  const parts = path.split(CLASS_PART_SEPARATOR);
  const len = parts.length;
  for (let i = 0; i < len; i++) {
    const part = parts[i];
    let next = current.nextPart.get(part);
    if (!next) {
      next = createClassPartObject();
      current.nextPart.set(part, next);
    }
    current = next;
  }
  return current;
};
var isThemeGetter = (func) => "isThemeGetter" in func && func.isThemeGetter === true;
var createLruCache = (maxCacheSize) => {
  if (maxCacheSize < 1) {
    return {
      get: () => void 0,
      set: () => {
      }
    };
  }
  let cacheSize = 0;
  let cache = /* @__PURE__ */ Object.create(null);
  let previousCache = /* @__PURE__ */ Object.create(null);
  const update = (key, value) => {
    cache[key] = value;
    cacheSize++;
    if (cacheSize > maxCacheSize) {
      cacheSize = 0;
      previousCache = cache;
      cache = /* @__PURE__ */ Object.create(null);
    }
  };
  return {
    get(key) {
      let value = cache[key];
      if (value !== void 0) {
        return value;
      }
      if ((value = previousCache[key]) !== void 0) {
        update(key, value);
        return value;
      }
    },
    set(key, value) {
      if (key in cache) {
        cache[key] = value;
      } else {
        update(key, value);
      }
    }
  };
};
var IMPORTANT_MODIFIER = "!";
var MODIFIER_SEPARATOR = ":";
var EMPTY_MODIFIERS = [];
var createResultObject = (modifiers, hasImportantModifier, baseClassName, maybePostfixModifierPosition, isExternal) => ({
  modifiers,
  hasImportantModifier,
  baseClassName,
  maybePostfixModifierPosition,
  isExternal
});
var createParseClassName = (config) => {
  const {
    prefix,
    experimentalParseClassName
  } = config;
  let parseClassName = (className) => {
    const modifiers = [];
    let bracketDepth = 0;
    let parenDepth = 0;
    let modifierStart = 0;
    let postfixModifierPosition;
    const len = className.length;
    for (let index = 0; index < len; index++) {
      const currentCharacter = className[index];
      if (bracketDepth === 0 && parenDepth === 0) {
        if (currentCharacter === MODIFIER_SEPARATOR) {
          modifiers.push(className.slice(modifierStart, index));
          modifierStart = index + 1;
          continue;
        }
        if (currentCharacter === "/") {
          postfixModifierPosition = index;
          continue;
        }
      }
      if (currentCharacter === "[") bracketDepth++;
      else if (currentCharacter === "]") bracketDepth--;
      else if (currentCharacter === "(") parenDepth++;
      else if (currentCharacter === ")") parenDepth--;
    }
    const baseClassNameWithImportantModifier = modifiers.length === 0 ? className : className.slice(modifierStart);
    let baseClassName = baseClassNameWithImportantModifier;
    let hasImportantModifier = false;
    if (baseClassNameWithImportantModifier.endsWith(IMPORTANT_MODIFIER)) {
      baseClassName = baseClassNameWithImportantModifier.slice(0, -1);
      hasImportantModifier = true;
    } else if (
      /**
       * In Tailwind CSS v3 the important modifier was at the start of the base class name. This is still supported for legacy reasons.
       * @see https://github.com/dcastil/tailwind-merge/issues/513#issuecomment-2614029864
       */
      baseClassNameWithImportantModifier.startsWith(IMPORTANT_MODIFIER)
    ) {
      baseClassName = baseClassNameWithImportantModifier.slice(1);
      hasImportantModifier = true;
    }
    const maybePostfixModifierPosition = postfixModifierPosition && postfixModifierPosition > modifierStart ? postfixModifierPosition - modifierStart : void 0;
    return createResultObject(modifiers, hasImportantModifier, baseClassName, maybePostfixModifierPosition);
  };
  if (prefix) {
    const fullPrefix = prefix + MODIFIER_SEPARATOR;
    const parseClassNameOriginal = parseClassName;
    parseClassName = (className) => className.startsWith(fullPrefix) ? parseClassNameOriginal(className.slice(fullPrefix.length)) : createResultObject(EMPTY_MODIFIERS, false, className, void 0, true);
  }
  if (experimentalParseClassName) {
    const parseClassNameOriginal = parseClassName;
    parseClassName = (className) => experimentalParseClassName({
      className,
      parseClassName: parseClassNameOriginal
    });
  }
  return parseClassName;
};
var createSortModifiers = (config) => {
  const modifierWeights = /* @__PURE__ */ new Map();
  config.orderSensitiveModifiers.forEach((mod, index) => {
    modifierWeights.set(mod, 1e6 + index);
  });
  return (modifiers) => {
    const result = [];
    let currentSegment = [];
    for (let i = 0; i < modifiers.length; i++) {
      const modifier = modifiers[i];
      const isArbitrary = modifier[0] === "[";
      const isOrderSensitive = modifierWeights.has(modifier);
      if (isArbitrary || isOrderSensitive) {
        if (currentSegment.length > 0) {
          currentSegment.sort();
          result.push(...currentSegment);
          currentSegment = [];
        }
        result.push(modifier);
      } else {
        currentSegment.push(modifier);
      }
    }
    if (currentSegment.length > 0) {
      currentSegment.sort();
      result.push(...currentSegment);
    }
    return result;
  };
};
var createConfigUtils = (config) => ({
  cache: createLruCache(config.cacheSize),
  parseClassName: createParseClassName(config),
  sortModifiers: createSortModifiers(config),
  ...createClassGroupUtils(config)
});
var SPLIT_CLASSES_REGEX = /\s+/;
var mergeClassList = (classList, configUtils) => {
  const {
    parseClassName,
    getClassGroupId,
    getConflictingClassGroupIds,
    sortModifiers
  } = configUtils;
  const classGroupsInConflict = [];
  const classNames = classList.trim().split(SPLIT_CLASSES_REGEX);
  let result = "";
  for (let index = classNames.length - 1; index >= 0; index -= 1) {
    const originalClassName = classNames[index];
    const {
      isExternal,
      modifiers,
      hasImportantModifier,
      baseClassName,
      maybePostfixModifierPosition
    } = parseClassName(originalClassName);
    if (isExternal) {
      result = originalClassName + (result.length > 0 ? " " + result : result);
      continue;
    }
    let hasPostfixModifier = !!maybePostfixModifierPosition;
    let classGroupId = getClassGroupId(hasPostfixModifier ? baseClassName.substring(0, maybePostfixModifierPosition) : baseClassName);
    if (!classGroupId) {
      if (!hasPostfixModifier) {
        result = originalClassName + (result.length > 0 ? " " + result : result);
        continue;
      }
      classGroupId = getClassGroupId(baseClassName);
      if (!classGroupId) {
        result = originalClassName + (result.length > 0 ? " " + result : result);
        continue;
      }
      hasPostfixModifier = false;
    }
    const variantModifier = modifiers.length === 0 ? "" : modifiers.length === 1 ? modifiers[0] : sortModifiers(modifiers).join(":");
    const modifierId = hasImportantModifier ? variantModifier + IMPORTANT_MODIFIER : variantModifier;
    const classId = modifierId + classGroupId;
    if (classGroupsInConflict.indexOf(classId) > -1) {
      continue;
    }
    classGroupsInConflict.push(classId);
    const conflictGroups = getConflictingClassGroupIds(classGroupId, hasPostfixModifier);
    for (let i = 0; i < conflictGroups.length; ++i) {
      const group = conflictGroups[i];
      classGroupsInConflict.push(modifierId + group);
    }
    result = originalClassName + (result.length > 0 ? " " + result : result);
  }
  return result;
};
var twJoin = (...classLists) => {
  let index = 0;
  let argument;
  let resolvedValue;
  let string = "";
  while (index < classLists.length) {
    if (argument = classLists[index++]) {
      if (resolvedValue = toValue(argument)) {
        string && (string += " ");
        string += resolvedValue;
      }
    }
  }
  return string;
};
var toValue = (mix) => {
  if (typeof mix === "string") {
    return mix;
  }
  let resolvedValue;
  let string = "";
  for (let k = 0; k < mix.length; k++) {
    if (mix[k]) {
      if (resolvedValue = toValue(mix[k])) {
        string && (string += " ");
        string += resolvedValue;
      }
    }
  }
  return string;
};
var createTailwindMerge = (createConfigFirst, ...createConfigRest) => {
  let configUtils;
  let cacheGet;
  let cacheSet;
  let functionToCall;
  const initTailwindMerge = (classList) => {
    const config = createConfigRest.reduce((previousConfig, createConfigCurrent) => createConfigCurrent(previousConfig), createConfigFirst());
    configUtils = createConfigUtils(config);
    cacheGet = configUtils.cache.get;
    cacheSet = configUtils.cache.set;
    functionToCall = tailwindMerge;
    return tailwindMerge(classList);
  };
  const tailwindMerge = (classList) => {
    const cachedResult = cacheGet(classList);
    if (cachedResult) {
      return cachedResult;
    }
    const result = mergeClassList(classList, configUtils);
    cacheSet(classList, result);
    return result;
  };
  functionToCall = initTailwindMerge;
  return (...args) => functionToCall(twJoin(...args));
};
var fallbackThemeArr = [];
var fromTheme = (key) => {
  const themeGetter = (theme) => theme[key] || fallbackThemeArr;
  themeGetter.isThemeGetter = true;
  return themeGetter;
};
var arbitraryValueRegex = /^\[(?:(\w[\w-]*):)?(.+)\]$/i;
var arbitraryVariableRegex = /^\((?:(\w[\w-]*):)?(.+)\)$/i;
var fractionRegex = /^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/;
var tshirtUnitRegex = /^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/;
var lengthUnitRegex = /\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/;
var colorFunctionRegex = /^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/;
var shadowRegex = /^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/;
var imageRegex = /^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/;
var isFraction = (value) => fractionRegex.test(value);
var isNumber = (value) => !!value && !Number.isNaN(Number(value));
var isInteger = (value) => !!value && Number.isInteger(Number(value));
var isPercent = (value) => value.endsWith("%") && isNumber(value.slice(0, -1));
var isTshirtSize = (value) => tshirtUnitRegex.test(value);
var isAny = () => true;
var isLengthOnly = (value) => (
  // `colorFunctionRegex` check is necessary because color functions can have percentages in them which which would be incorrectly classified as lengths.
  // For example, `hsl(0 0% 0%)` would be classified as a length without this check.
  // I could also use lookbehind assertion in `lengthUnitRegex` but that isn't supported widely enough.
  lengthUnitRegex.test(value) && !colorFunctionRegex.test(value)
);
var isNever = () => false;
var isShadow = (value) => shadowRegex.test(value);
var isImage = (value) => imageRegex.test(value);
var isAnyNonArbitrary = (value) => !isArbitraryValue(value) && !isArbitraryVariable(value);
var isArbitrarySize = (value) => getIsArbitraryValue(value, isLabelSize, isNever);
var isArbitraryValue = (value) => arbitraryValueRegex.test(value);
var isArbitraryLength = (value) => getIsArbitraryValue(value, isLabelLength, isLengthOnly);
var isArbitraryNumber = (value) => getIsArbitraryValue(value, isLabelNumber, isNumber);
var isArbitraryWeight = (value) => getIsArbitraryValue(value, isLabelWeight, isAny);
var isArbitraryFamilyName = (value) => getIsArbitraryValue(value, isLabelFamilyName, isNever);
var isArbitraryPosition = (value) => getIsArbitraryValue(value, isLabelPosition, isNever);
var isArbitraryImage = (value) => getIsArbitraryValue(value, isLabelImage, isImage);
var isArbitraryShadow = (value) => getIsArbitraryValue(value, isLabelShadow, isShadow);
var isArbitraryVariable = (value) => arbitraryVariableRegex.test(value);
var isArbitraryVariableLength = (value) => getIsArbitraryVariable(value, isLabelLength);
var isArbitraryVariableFamilyName = (value) => getIsArbitraryVariable(value, isLabelFamilyName);
var isArbitraryVariablePosition = (value) => getIsArbitraryVariable(value, isLabelPosition);
var isArbitraryVariableSize = (value) => getIsArbitraryVariable(value, isLabelSize);
var isArbitraryVariableImage = (value) => getIsArbitraryVariable(value, isLabelImage);
var isArbitraryVariableShadow = (value) => getIsArbitraryVariable(value, isLabelShadow, true);
var isArbitraryVariableWeight = (value) => getIsArbitraryVariable(value, isLabelWeight, true);
var getIsArbitraryValue = (value, testLabel, testValue) => {
  const result = arbitraryValueRegex.exec(value);
  if (result) {
    if (result[1]) {
      return testLabel(result[1]);
    }
    return testValue(result[2]);
  }
  return false;
};
var getIsArbitraryVariable = (value, testLabel, shouldMatchNoLabel = false) => {
  const result = arbitraryVariableRegex.exec(value);
  if (result) {
    if (result[1]) {
      return testLabel(result[1]);
    }
    return shouldMatchNoLabel;
  }
  return false;
};
var isLabelPosition = (label) => label === "position" || label === "percentage";
var isLabelImage = (label) => label === "image" || label === "url";
var isLabelSize = (label) => label === "length" || label === "size" || label === "bg-size";
var isLabelLength = (label) => label === "length";
var isLabelNumber = (label) => label === "number";
var isLabelFamilyName = (label) => label === "family-name";
var isLabelWeight = (label) => label === "number" || label === "weight";
var isLabelShadow = (label) => label === "shadow";
var getDefaultConfig = () => {
  const themeColor = fromTheme("color");
  const themeFont = fromTheme("font");
  const themeText = fromTheme("text");
  const themeFontWeight = fromTheme("font-weight");
  const themeTracking = fromTheme("tracking");
  const themeLeading = fromTheme("leading");
  const themeBreakpoint = fromTheme("breakpoint");
  const themeContainer = fromTheme("container");
  const themeSpacing = fromTheme("spacing");
  const themeRadius = fromTheme("radius");
  const themeShadow = fromTheme("shadow");
  const themeInsetShadow = fromTheme("inset-shadow");
  const themeTextShadow = fromTheme("text-shadow");
  const themeDropShadow = fromTheme("drop-shadow");
  const themeBlur = fromTheme("blur");
  const themePerspective = fromTheme("perspective");
  const themeAspect = fromTheme("aspect");
  const themeEase = fromTheme("ease");
  const themeAnimate = fromTheme("animate");
  const scaleBreak = () => ["auto", "avoid", "all", "avoid-page", "page", "left", "right", "column"];
  const scalePosition = () => [
    "center",
    "top",
    "bottom",
    "left",
    "right",
    "top-left",
    // Deprecated since Tailwind CSS v4.1.0, see https://github.com/tailwindlabs/tailwindcss/pull/17378
    "left-top",
    "top-right",
    // Deprecated since Tailwind CSS v4.1.0, see https://github.com/tailwindlabs/tailwindcss/pull/17378
    "right-top",
    "bottom-right",
    // Deprecated since Tailwind CSS v4.1.0, see https://github.com/tailwindlabs/tailwindcss/pull/17378
    "right-bottom",
    "bottom-left",
    // Deprecated since Tailwind CSS v4.1.0, see https://github.com/tailwindlabs/tailwindcss/pull/17378
    "left-bottom"
  ];
  const scalePositionWithArbitrary = () => [...scalePosition(), isArbitraryVariable, isArbitraryValue];
  const scaleOverflow = () => ["auto", "hidden", "clip", "visible", "scroll"];
  const scaleOverscroll = () => ["auto", "contain", "none"];
  const scaleUnambiguousSpacing = () => [isArbitraryVariable, isArbitraryValue, themeSpacing];
  const scaleInset = () => [isFraction, "full", "auto", ...scaleUnambiguousSpacing()];
  const scaleGridTemplateColsRows = () => [isInteger, "none", "subgrid", isArbitraryVariable, isArbitraryValue];
  const scaleGridColRowStartAndEnd = () => ["auto", {
    span: ["full", isInteger, isArbitraryVariable, isArbitraryValue]
  }, isInteger, isArbitraryVariable, isArbitraryValue];
  const scaleGridColRowStartOrEnd = () => [isInteger, "auto", isArbitraryVariable, isArbitraryValue];
  const scaleGridAutoColsRows = () => ["auto", "min", "max", "fr", isArbitraryVariable, isArbitraryValue];
  const scaleAlignPrimaryAxis = () => ["start", "end", "center", "between", "around", "evenly", "stretch", "baseline", "center-safe", "end-safe"];
  const scaleAlignSecondaryAxis = () => ["start", "end", "center", "stretch", "center-safe", "end-safe"];
  const scaleMargin = () => ["auto", ...scaleUnambiguousSpacing()];
  const scaleSizing = () => [isFraction, "auto", "full", "dvw", "dvh", "lvw", "lvh", "svw", "svh", "min", "max", "fit", ...scaleUnambiguousSpacing()];
  const scaleSizingInline = () => [isFraction, "screen", "full", "dvw", "lvw", "svw", "min", "max", "fit", ...scaleUnambiguousSpacing()];
  const scaleSizingBlock = () => [isFraction, "screen", "full", "lh", "dvh", "lvh", "svh", "min", "max", "fit", ...scaleUnambiguousSpacing()];
  const scaleColor = () => [themeColor, isArbitraryVariable, isArbitraryValue];
  const scaleBgPosition = () => [...scalePosition(), isArbitraryVariablePosition, isArbitraryPosition, {
    position: [isArbitraryVariable, isArbitraryValue]
  }];
  const scaleBgRepeat = () => ["no-repeat", {
    repeat: ["", "x", "y", "space", "round"]
  }];
  const scaleBgSize = () => ["auto", "cover", "contain", isArbitraryVariableSize, isArbitrarySize, {
    size: [isArbitraryVariable, isArbitraryValue]
  }];
  const scaleGradientStopPosition = () => [isPercent, isArbitraryVariableLength, isArbitraryLength];
  const scaleRadius = () => [
    // Deprecated since Tailwind CSS v4.0.0
    "",
    "none",
    "full",
    themeRadius,
    isArbitraryVariable,
    isArbitraryValue
  ];
  const scaleBorderWidth = () => ["", isNumber, isArbitraryVariableLength, isArbitraryLength];
  const scaleLineStyle = () => ["solid", "dashed", "dotted", "double"];
  const scaleBlendMode = () => ["normal", "multiply", "screen", "overlay", "darken", "lighten", "color-dodge", "color-burn", "hard-light", "soft-light", "difference", "exclusion", "hue", "saturation", "color", "luminosity"];
  const scaleMaskImagePosition = () => [isNumber, isPercent, isArbitraryVariablePosition, isArbitraryPosition];
  const scaleBlur = () => [
    // Deprecated since Tailwind CSS v4.0.0
    "",
    "none",
    themeBlur,
    isArbitraryVariable,
    isArbitraryValue
  ];
  const scaleRotate = () => ["none", isNumber, isArbitraryVariable, isArbitraryValue];
  const scaleScale = () => ["none", isNumber, isArbitraryVariable, isArbitraryValue];
  const scaleSkew = () => [isNumber, isArbitraryVariable, isArbitraryValue];
  const scaleTranslate = () => [isFraction, "full", ...scaleUnambiguousSpacing()];
  return {
    cacheSize: 500,
    theme: {
      animate: ["spin", "ping", "pulse", "bounce"],
      aspect: ["video"],
      blur: [isTshirtSize],
      breakpoint: [isTshirtSize],
      color: [isAny],
      container: [isTshirtSize],
      "drop-shadow": [isTshirtSize],
      ease: ["in", "out", "in-out"],
      font: [isAnyNonArbitrary],
      "font-weight": ["thin", "extralight", "light", "normal", "medium", "semibold", "bold", "extrabold", "black"],
      "inset-shadow": [isTshirtSize],
      leading: ["none", "tight", "snug", "normal", "relaxed", "loose"],
      perspective: ["dramatic", "near", "normal", "midrange", "distant", "none"],
      radius: [isTshirtSize],
      shadow: [isTshirtSize],
      spacing: ["px", isNumber],
      text: [isTshirtSize],
      "text-shadow": [isTshirtSize],
      tracking: ["tighter", "tight", "normal", "wide", "wider", "widest"]
    },
    classGroups: {
      // --------------
      // --- Layout ---
      // --------------
      /**
       * Aspect Ratio
       * @see https://tailwindcss.com/docs/aspect-ratio
       */
      aspect: [{
        aspect: ["auto", "square", isFraction, isArbitraryValue, isArbitraryVariable, themeAspect]
      }],
      /**
       * Container
       * @see https://tailwindcss.com/docs/container
       * @deprecated since Tailwind CSS v4.0.0
       */
      container: ["container"],
      /**
       * Columns
       * @see https://tailwindcss.com/docs/columns
       */
      columns: [{
        columns: [isNumber, isArbitraryValue, isArbitraryVariable, themeContainer]
      }],
      /**
       * Break After
       * @see https://tailwindcss.com/docs/break-after
       */
      "break-after": [{
        "break-after": scaleBreak()
      }],
      /**
       * Break Before
       * @see https://tailwindcss.com/docs/break-before
       */
      "break-before": [{
        "break-before": scaleBreak()
      }],
      /**
       * Break Inside
       * @see https://tailwindcss.com/docs/break-inside
       */
      "break-inside": [{
        "break-inside": ["auto", "avoid", "avoid-page", "avoid-column"]
      }],
      /**
       * Box Decoration Break
       * @see https://tailwindcss.com/docs/box-decoration-break
       */
      "box-decoration": [{
        "box-decoration": ["slice", "clone"]
      }],
      /**
       * Box Sizing
       * @see https://tailwindcss.com/docs/box-sizing
       */
      box: [{
        box: ["border", "content"]
      }],
      /**
       * Display
       * @see https://tailwindcss.com/docs/display
       */
      display: ["block", "inline-block", "inline", "flex", "inline-flex", "table", "inline-table", "table-caption", "table-cell", "table-column", "table-column-group", "table-footer-group", "table-header-group", "table-row-group", "table-row", "flow-root", "grid", "inline-grid", "contents", "list-item", "hidden"],
      /**
       * Screen Reader Only
       * @see https://tailwindcss.com/docs/display#screen-reader-only
       */
      sr: ["sr-only", "not-sr-only"],
      /**
       * Floats
       * @see https://tailwindcss.com/docs/float
       */
      float: [{
        float: ["right", "left", "none", "start", "end"]
      }],
      /**
       * Clear
       * @see https://tailwindcss.com/docs/clear
       */
      clear: [{
        clear: ["left", "right", "both", "none", "start", "end"]
      }],
      /**
       * Isolation
       * @see https://tailwindcss.com/docs/isolation
       */
      isolation: ["isolate", "isolation-auto"],
      /**
       * Object Fit
       * @see https://tailwindcss.com/docs/object-fit
       */
      "object-fit": [{
        object: ["contain", "cover", "fill", "none", "scale-down"]
      }],
      /**
       * Object Position
       * @see https://tailwindcss.com/docs/object-position
       */
      "object-position": [{
        object: scalePositionWithArbitrary()
      }],
      /**
       * Overflow
       * @see https://tailwindcss.com/docs/overflow
       */
      overflow: [{
        overflow: scaleOverflow()
      }],
      /**
       * Overflow X
       * @see https://tailwindcss.com/docs/overflow
       */
      "overflow-x": [{
        "overflow-x": scaleOverflow()
      }],
      /**
       * Overflow Y
       * @see https://tailwindcss.com/docs/overflow
       */
      "overflow-y": [{
        "overflow-y": scaleOverflow()
      }],
      /**
       * Overscroll Behavior
       * @see https://tailwindcss.com/docs/overscroll-behavior
       */
      overscroll: [{
        overscroll: scaleOverscroll()
      }],
      /**
       * Overscroll Behavior X
       * @see https://tailwindcss.com/docs/overscroll-behavior
       */
      "overscroll-x": [{
        "overscroll-x": scaleOverscroll()
      }],
      /**
       * Overscroll Behavior Y
       * @see https://tailwindcss.com/docs/overscroll-behavior
       */
      "overscroll-y": [{
        "overscroll-y": scaleOverscroll()
      }],
      /**
       * Position
       * @see https://tailwindcss.com/docs/position
       */
      position: ["static", "fixed", "absolute", "relative", "sticky"],
      /**
       * Inset
       * @see https://tailwindcss.com/docs/top-right-bottom-left
       */
      inset: [{
        inset: scaleInset()
      }],
      /**
       * Inset Inline
       * @see https://tailwindcss.com/docs/top-right-bottom-left
       */
      "inset-x": [{
        "inset-x": scaleInset()
      }],
      /**
       * Inset Block
       * @see https://tailwindcss.com/docs/top-right-bottom-left
       */
      "inset-y": [{
        "inset-y": scaleInset()
      }],
      /**
       * Inset Inline Start
       * @see https://tailwindcss.com/docs/top-right-bottom-left
       * @todo class group will be renamed to `inset-s` in next major release
       */
      start: [{
        "inset-s": scaleInset(),
        /**
         * @deprecated since Tailwind CSS v4.2.0 in favor of `inset-s-*` utilities.
         * @see https://github.com/tailwindlabs/tailwindcss/pull/19613
         */
        start: scaleInset()
      }],
      /**
       * Inset Inline End
       * @see https://tailwindcss.com/docs/top-right-bottom-left
       * @todo class group will be renamed to `inset-e` in next major release
       */
      end: [{
        "inset-e": scaleInset(),
        /**
         * @deprecated since Tailwind CSS v4.2.0 in favor of `inset-e-*` utilities.
         * @see https://github.com/tailwindlabs/tailwindcss/pull/19613
         */
        end: scaleInset()
      }],
      /**
       * Inset Block Start
       * @see https://tailwindcss.com/docs/top-right-bottom-left
       */
      "inset-bs": [{
        "inset-bs": scaleInset()
      }],
      /**
       * Inset Block End
       * @see https://tailwindcss.com/docs/top-right-bottom-left
       */
      "inset-be": [{
        "inset-be": scaleInset()
      }],
      /**
       * Top
       * @see https://tailwindcss.com/docs/top-right-bottom-left
       */
      top: [{
        top: scaleInset()
      }],
      /**
       * Right
       * @see https://tailwindcss.com/docs/top-right-bottom-left
       */
      right: [{
        right: scaleInset()
      }],
      /**
       * Bottom
       * @see https://tailwindcss.com/docs/top-right-bottom-left
       */
      bottom: [{
        bottom: scaleInset()
      }],
      /**
       * Left
       * @see https://tailwindcss.com/docs/top-right-bottom-left
       */
      left: [{
        left: scaleInset()
      }],
      /**
       * Visibility
       * @see https://tailwindcss.com/docs/visibility
       */
      visibility: ["visible", "invisible", "collapse"],
      /**
       * Z-Index
       * @see https://tailwindcss.com/docs/z-index
       */
      z: [{
        z: [isInteger, "auto", isArbitraryVariable, isArbitraryValue]
      }],
      // ------------------------
      // --- Flexbox and Grid ---
      // ------------------------
      /**
       * Flex Basis
       * @see https://tailwindcss.com/docs/flex-basis
       */
      basis: [{
        basis: [isFraction, "full", "auto", themeContainer, ...scaleUnambiguousSpacing()]
      }],
      /**
       * Flex Direction
       * @see https://tailwindcss.com/docs/flex-direction
       */
      "flex-direction": [{
        flex: ["row", "row-reverse", "col", "col-reverse"]
      }],
      /**
       * Flex Wrap
       * @see https://tailwindcss.com/docs/flex-wrap
       */
      "flex-wrap": [{
        flex: ["nowrap", "wrap", "wrap-reverse"]
      }],
      /**
       * Flex
       * @see https://tailwindcss.com/docs/flex
       */
      flex: [{
        flex: [isNumber, isFraction, "auto", "initial", "none", isArbitraryValue]
      }],
      /**
       * Flex Grow
       * @see https://tailwindcss.com/docs/flex-grow
       */
      grow: [{
        grow: ["", isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Flex Shrink
       * @see https://tailwindcss.com/docs/flex-shrink
       */
      shrink: [{
        shrink: ["", isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Order
       * @see https://tailwindcss.com/docs/order
       */
      order: [{
        order: [isInteger, "first", "last", "none", isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Grid Template Columns
       * @see https://tailwindcss.com/docs/grid-template-columns
       */
      "grid-cols": [{
        "grid-cols": scaleGridTemplateColsRows()
      }],
      /**
       * Grid Column Start / End
       * @see https://tailwindcss.com/docs/grid-column
       */
      "col-start-end": [{
        col: scaleGridColRowStartAndEnd()
      }],
      /**
       * Grid Column Start
       * @see https://tailwindcss.com/docs/grid-column
       */
      "col-start": [{
        "col-start": scaleGridColRowStartOrEnd()
      }],
      /**
       * Grid Column End
       * @see https://tailwindcss.com/docs/grid-column
       */
      "col-end": [{
        "col-end": scaleGridColRowStartOrEnd()
      }],
      /**
       * Grid Template Rows
       * @see https://tailwindcss.com/docs/grid-template-rows
       */
      "grid-rows": [{
        "grid-rows": scaleGridTemplateColsRows()
      }],
      /**
       * Grid Row Start / End
       * @see https://tailwindcss.com/docs/grid-row
       */
      "row-start-end": [{
        row: scaleGridColRowStartAndEnd()
      }],
      /**
       * Grid Row Start
       * @see https://tailwindcss.com/docs/grid-row
       */
      "row-start": [{
        "row-start": scaleGridColRowStartOrEnd()
      }],
      /**
       * Grid Row End
       * @see https://tailwindcss.com/docs/grid-row
       */
      "row-end": [{
        "row-end": scaleGridColRowStartOrEnd()
      }],
      /**
       * Grid Auto Flow
       * @see https://tailwindcss.com/docs/grid-auto-flow
       */
      "grid-flow": [{
        "grid-flow": ["row", "col", "dense", "row-dense", "col-dense"]
      }],
      /**
       * Grid Auto Columns
       * @see https://tailwindcss.com/docs/grid-auto-columns
       */
      "auto-cols": [{
        "auto-cols": scaleGridAutoColsRows()
      }],
      /**
       * Grid Auto Rows
       * @see https://tailwindcss.com/docs/grid-auto-rows
       */
      "auto-rows": [{
        "auto-rows": scaleGridAutoColsRows()
      }],
      /**
       * Gap
       * @see https://tailwindcss.com/docs/gap
       */
      gap: [{
        gap: scaleUnambiguousSpacing()
      }],
      /**
       * Gap X
       * @see https://tailwindcss.com/docs/gap
       */
      "gap-x": [{
        "gap-x": scaleUnambiguousSpacing()
      }],
      /**
       * Gap Y
       * @see https://tailwindcss.com/docs/gap
       */
      "gap-y": [{
        "gap-y": scaleUnambiguousSpacing()
      }],
      /**
       * Justify Content
       * @see https://tailwindcss.com/docs/justify-content
       */
      "justify-content": [{
        justify: [...scaleAlignPrimaryAxis(), "normal"]
      }],
      /**
       * Justify Items
       * @see https://tailwindcss.com/docs/justify-items
       */
      "justify-items": [{
        "justify-items": [...scaleAlignSecondaryAxis(), "normal"]
      }],
      /**
       * Justify Self
       * @see https://tailwindcss.com/docs/justify-self
       */
      "justify-self": [{
        "justify-self": ["auto", ...scaleAlignSecondaryAxis()]
      }],
      /**
       * Align Content
       * @see https://tailwindcss.com/docs/align-content
       */
      "align-content": [{
        content: ["normal", ...scaleAlignPrimaryAxis()]
      }],
      /**
       * Align Items
       * @see https://tailwindcss.com/docs/align-items
       */
      "align-items": [{
        items: [...scaleAlignSecondaryAxis(), {
          baseline: ["", "last"]
        }]
      }],
      /**
       * Align Self
       * @see https://tailwindcss.com/docs/align-self
       */
      "align-self": [{
        self: ["auto", ...scaleAlignSecondaryAxis(), {
          baseline: ["", "last"]
        }]
      }],
      /**
       * Place Content
       * @see https://tailwindcss.com/docs/place-content
       */
      "place-content": [{
        "place-content": scaleAlignPrimaryAxis()
      }],
      /**
       * Place Items
       * @see https://tailwindcss.com/docs/place-items
       */
      "place-items": [{
        "place-items": [...scaleAlignSecondaryAxis(), "baseline"]
      }],
      /**
       * Place Self
       * @see https://tailwindcss.com/docs/place-self
       */
      "place-self": [{
        "place-self": ["auto", ...scaleAlignSecondaryAxis()]
      }],
      // Spacing
      /**
       * Padding
       * @see https://tailwindcss.com/docs/padding
       */
      p: [{
        p: scaleUnambiguousSpacing()
      }],
      /**
       * Padding Inline
       * @see https://tailwindcss.com/docs/padding
       */
      px: [{
        px: scaleUnambiguousSpacing()
      }],
      /**
       * Padding Block
       * @see https://tailwindcss.com/docs/padding
       */
      py: [{
        py: scaleUnambiguousSpacing()
      }],
      /**
       * Padding Inline Start
       * @see https://tailwindcss.com/docs/padding
       */
      ps: [{
        ps: scaleUnambiguousSpacing()
      }],
      /**
       * Padding Inline End
       * @see https://tailwindcss.com/docs/padding
       */
      pe: [{
        pe: scaleUnambiguousSpacing()
      }],
      /**
       * Padding Block Start
       * @see https://tailwindcss.com/docs/padding
       */
      pbs: [{
        pbs: scaleUnambiguousSpacing()
      }],
      /**
       * Padding Block End
       * @see https://tailwindcss.com/docs/padding
       */
      pbe: [{
        pbe: scaleUnambiguousSpacing()
      }],
      /**
       * Padding Top
       * @see https://tailwindcss.com/docs/padding
       */
      pt: [{
        pt: scaleUnambiguousSpacing()
      }],
      /**
       * Padding Right
       * @see https://tailwindcss.com/docs/padding
       */
      pr: [{
        pr: scaleUnambiguousSpacing()
      }],
      /**
       * Padding Bottom
       * @see https://tailwindcss.com/docs/padding
       */
      pb: [{
        pb: scaleUnambiguousSpacing()
      }],
      /**
       * Padding Left
       * @see https://tailwindcss.com/docs/padding
       */
      pl: [{
        pl: scaleUnambiguousSpacing()
      }],
      /**
       * Margin
       * @see https://tailwindcss.com/docs/margin
       */
      m: [{
        m: scaleMargin()
      }],
      /**
       * Margin Inline
       * @see https://tailwindcss.com/docs/margin
       */
      mx: [{
        mx: scaleMargin()
      }],
      /**
       * Margin Block
       * @see https://tailwindcss.com/docs/margin
       */
      my: [{
        my: scaleMargin()
      }],
      /**
       * Margin Inline Start
       * @see https://tailwindcss.com/docs/margin
       */
      ms: [{
        ms: scaleMargin()
      }],
      /**
       * Margin Inline End
       * @see https://tailwindcss.com/docs/margin
       */
      me: [{
        me: scaleMargin()
      }],
      /**
       * Margin Block Start
       * @see https://tailwindcss.com/docs/margin
       */
      mbs: [{
        mbs: scaleMargin()
      }],
      /**
       * Margin Block End
       * @see https://tailwindcss.com/docs/margin
       */
      mbe: [{
        mbe: scaleMargin()
      }],
      /**
       * Margin Top
       * @see https://tailwindcss.com/docs/margin
       */
      mt: [{
        mt: scaleMargin()
      }],
      /**
       * Margin Right
       * @see https://tailwindcss.com/docs/margin
       */
      mr: [{
        mr: scaleMargin()
      }],
      /**
       * Margin Bottom
       * @see https://tailwindcss.com/docs/margin
       */
      mb: [{
        mb: scaleMargin()
      }],
      /**
       * Margin Left
       * @see https://tailwindcss.com/docs/margin
       */
      ml: [{
        ml: scaleMargin()
      }],
      /**
       * Space Between X
       * @see https://tailwindcss.com/docs/margin#adding-space-between-children
       */
      "space-x": [{
        "space-x": scaleUnambiguousSpacing()
      }],
      /**
       * Space Between X Reverse
       * @see https://tailwindcss.com/docs/margin#adding-space-between-children
       */
      "space-x-reverse": ["space-x-reverse"],
      /**
       * Space Between Y
       * @see https://tailwindcss.com/docs/margin#adding-space-between-children
       */
      "space-y": [{
        "space-y": scaleUnambiguousSpacing()
      }],
      /**
       * Space Between Y Reverse
       * @see https://tailwindcss.com/docs/margin#adding-space-between-children
       */
      "space-y-reverse": ["space-y-reverse"],
      // --------------
      // --- Sizing ---
      // --------------
      /**
       * Size
       * @see https://tailwindcss.com/docs/width#setting-both-width-and-height
       */
      size: [{
        size: scaleSizing()
      }],
      /**
       * Inline Size
       * @see https://tailwindcss.com/docs/width
       */
      "inline-size": [{
        inline: ["auto", ...scaleSizingInline()]
      }],
      /**
       * Min-Inline Size
       * @see https://tailwindcss.com/docs/min-width
       */
      "min-inline-size": [{
        "min-inline": ["auto", ...scaleSizingInline()]
      }],
      /**
       * Max-Inline Size
       * @see https://tailwindcss.com/docs/max-width
       */
      "max-inline-size": [{
        "max-inline": ["none", ...scaleSizingInline()]
      }],
      /**
       * Block Size
       * @see https://tailwindcss.com/docs/height
       */
      "block-size": [{
        block: ["auto", ...scaleSizingBlock()]
      }],
      /**
       * Min-Block Size
       * @see https://tailwindcss.com/docs/min-height
       */
      "min-block-size": [{
        "min-block": ["auto", ...scaleSizingBlock()]
      }],
      /**
       * Max-Block Size
       * @see https://tailwindcss.com/docs/max-height
       */
      "max-block-size": [{
        "max-block": ["none", ...scaleSizingBlock()]
      }],
      /**
       * Width
       * @see https://tailwindcss.com/docs/width
       */
      w: [{
        w: [themeContainer, "screen", ...scaleSizing()]
      }],
      /**
       * Min-Width
       * @see https://tailwindcss.com/docs/min-width
       */
      "min-w": [{
        "min-w": [
          themeContainer,
          "screen",
          /** Deprecated. @see https://github.com/tailwindlabs/tailwindcss.com/issues/2027#issuecomment-2620152757 */
          "none",
          ...scaleSizing()
        ]
      }],
      /**
       * Max-Width
       * @see https://tailwindcss.com/docs/max-width
       */
      "max-w": [{
        "max-w": [
          themeContainer,
          "screen",
          "none",
          /** Deprecated since Tailwind CSS v4.0.0. @see https://github.com/tailwindlabs/tailwindcss.com/issues/2027#issuecomment-2620152757 */
          "prose",
          /** Deprecated since Tailwind CSS v4.0.0. @see https://github.com/tailwindlabs/tailwindcss.com/issues/2027#issuecomment-2620152757 */
          {
            screen: [themeBreakpoint]
          },
          ...scaleSizing()
        ]
      }],
      /**
       * Height
       * @see https://tailwindcss.com/docs/height
       */
      h: [{
        h: ["screen", "lh", ...scaleSizing()]
      }],
      /**
       * Min-Height
       * @see https://tailwindcss.com/docs/min-height
       */
      "min-h": [{
        "min-h": ["screen", "lh", "none", ...scaleSizing()]
      }],
      /**
       * Max-Height
       * @see https://tailwindcss.com/docs/max-height
       */
      "max-h": [{
        "max-h": ["screen", "lh", ...scaleSizing()]
      }],
      // ------------------
      // --- Typography ---
      // ------------------
      /**
       * Font Size
       * @see https://tailwindcss.com/docs/font-size
       */
      "font-size": [{
        text: ["base", themeText, isArbitraryVariableLength, isArbitraryLength]
      }],
      /**
       * Font Smoothing
       * @see https://tailwindcss.com/docs/font-smoothing
       */
      "font-smoothing": ["antialiased", "subpixel-antialiased"],
      /**
       * Font Style
       * @see https://tailwindcss.com/docs/font-style
       */
      "font-style": ["italic", "not-italic"],
      /**
       * Font Weight
       * @see https://tailwindcss.com/docs/font-weight
       */
      "font-weight": [{
        font: [themeFontWeight, isArbitraryVariableWeight, isArbitraryWeight]
      }],
      /**
       * Font Stretch
       * @see https://tailwindcss.com/docs/font-stretch
       */
      "font-stretch": [{
        "font-stretch": ["ultra-condensed", "extra-condensed", "condensed", "semi-condensed", "normal", "semi-expanded", "expanded", "extra-expanded", "ultra-expanded", isPercent, isArbitraryValue]
      }],
      /**
       * Font Family
       * @see https://tailwindcss.com/docs/font-family
       */
      "font-family": [{
        font: [isArbitraryVariableFamilyName, isArbitraryFamilyName, themeFont]
      }],
      /**
       * Font Feature Settings
       * @see https://tailwindcss.com/docs/font-feature-settings
       */
      "font-features": [{
        "font-features": [isArbitraryValue]
      }],
      /**
       * Font Variant Numeric
       * @see https://tailwindcss.com/docs/font-variant-numeric
       */
      "fvn-normal": ["normal-nums"],
      /**
       * Font Variant Numeric
       * @see https://tailwindcss.com/docs/font-variant-numeric
       */
      "fvn-ordinal": ["ordinal"],
      /**
       * Font Variant Numeric
       * @see https://tailwindcss.com/docs/font-variant-numeric
       */
      "fvn-slashed-zero": ["slashed-zero"],
      /**
       * Font Variant Numeric
       * @see https://tailwindcss.com/docs/font-variant-numeric
       */
      "fvn-figure": ["lining-nums", "oldstyle-nums"],
      /**
       * Font Variant Numeric
       * @see https://tailwindcss.com/docs/font-variant-numeric
       */
      "fvn-spacing": ["proportional-nums", "tabular-nums"],
      /**
       * Font Variant Numeric
       * @see https://tailwindcss.com/docs/font-variant-numeric
       */
      "fvn-fraction": ["diagonal-fractions", "stacked-fractions"],
      /**
       * Letter Spacing
       * @see https://tailwindcss.com/docs/letter-spacing
       */
      tracking: [{
        tracking: [themeTracking, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Line Clamp
       * @see https://tailwindcss.com/docs/line-clamp
       */
      "line-clamp": [{
        "line-clamp": [isNumber, "none", isArbitraryVariable, isArbitraryNumber]
      }],
      /**
       * Line Height
       * @see https://tailwindcss.com/docs/line-height
       */
      leading: [{
        leading: [
          /** Deprecated since Tailwind CSS v4.0.0. @see https://github.com/tailwindlabs/tailwindcss.com/issues/2027#issuecomment-2620152757 */
          themeLeading,
          ...scaleUnambiguousSpacing()
        ]
      }],
      /**
       * List Style Image
       * @see https://tailwindcss.com/docs/list-style-image
       */
      "list-image": [{
        "list-image": ["none", isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * List Style Position
       * @see https://tailwindcss.com/docs/list-style-position
       */
      "list-style-position": [{
        list: ["inside", "outside"]
      }],
      /**
       * List Style Type
       * @see https://tailwindcss.com/docs/list-style-type
       */
      "list-style-type": [{
        list: ["disc", "decimal", "none", isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Text Alignment
       * @see https://tailwindcss.com/docs/text-align
       */
      "text-alignment": [{
        text: ["left", "center", "right", "justify", "start", "end"]
      }],
      /**
       * Placeholder Color
       * @deprecated since Tailwind CSS v3.0.0
       * @see https://v3.tailwindcss.com/docs/placeholder-color
       */
      "placeholder-color": [{
        placeholder: scaleColor()
      }],
      /**
       * Text Color
       * @see https://tailwindcss.com/docs/text-color
       */
      "text-color": [{
        text: scaleColor()
      }],
      /**
       * Text Decoration
       * @see https://tailwindcss.com/docs/text-decoration
       */
      "text-decoration": ["underline", "overline", "line-through", "no-underline"],
      /**
       * Text Decoration Style
       * @see https://tailwindcss.com/docs/text-decoration-style
       */
      "text-decoration-style": [{
        decoration: [...scaleLineStyle(), "wavy"]
      }],
      /**
       * Text Decoration Thickness
       * @see https://tailwindcss.com/docs/text-decoration-thickness
       */
      "text-decoration-thickness": [{
        decoration: [isNumber, "from-font", "auto", isArbitraryVariable, isArbitraryLength]
      }],
      /**
       * Text Decoration Color
       * @see https://tailwindcss.com/docs/text-decoration-color
       */
      "text-decoration-color": [{
        decoration: scaleColor()
      }],
      /**
       * Text Underline Offset
       * @see https://tailwindcss.com/docs/text-underline-offset
       */
      "underline-offset": [{
        "underline-offset": [isNumber, "auto", isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Text Transform
       * @see https://tailwindcss.com/docs/text-transform
       */
      "text-transform": ["uppercase", "lowercase", "capitalize", "normal-case"],
      /**
       * Text Overflow
       * @see https://tailwindcss.com/docs/text-overflow
       */
      "text-overflow": ["truncate", "text-ellipsis", "text-clip"],
      /**
       * Text Wrap
       * @see https://tailwindcss.com/docs/text-wrap
       */
      "text-wrap": [{
        text: ["wrap", "nowrap", "balance", "pretty"]
      }],
      /**
       * Text Indent
       * @see https://tailwindcss.com/docs/text-indent
       */
      indent: [{
        indent: scaleUnambiguousSpacing()
      }],
      /**
       * Vertical Alignment
       * @see https://tailwindcss.com/docs/vertical-align
       */
      "vertical-align": [{
        align: ["baseline", "top", "middle", "bottom", "text-top", "text-bottom", "sub", "super", isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Whitespace
       * @see https://tailwindcss.com/docs/whitespace
       */
      whitespace: [{
        whitespace: ["normal", "nowrap", "pre", "pre-line", "pre-wrap", "break-spaces"]
      }],
      /**
       * Word Break
       * @see https://tailwindcss.com/docs/word-break
       */
      break: [{
        break: ["normal", "words", "all", "keep"]
      }],
      /**
       * Overflow Wrap
       * @see https://tailwindcss.com/docs/overflow-wrap
       */
      wrap: [{
        wrap: ["break-word", "anywhere", "normal"]
      }],
      /**
       * Hyphens
       * @see https://tailwindcss.com/docs/hyphens
       */
      hyphens: [{
        hyphens: ["none", "manual", "auto"]
      }],
      /**
       * Content
       * @see https://tailwindcss.com/docs/content
       */
      content: [{
        content: ["none", isArbitraryVariable, isArbitraryValue]
      }],
      // -------------------
      // --- Backgrounds ---
      // -------------------
      /**
       * Background Attachment
       * @see https://tailwindcss.com/docs/background-attachment
       */
      "bg-attachment": [{
        bg: ["fixed", "local", "scroll"]
      }],
      /**
       * Background Clip
       * @see https://tailwindcss.com/docs/background-clip
       */
      "bg-clip": [{
        "bg-clip": ["border", "padding", "content", "text"]
      }],
      /**
       * Background Origin
       * @see https://tailwindcss.com/docs/background-origin
       */
      "bg-origin": [{
        "bg-origin": ["border", "padding", "content"]
      }],
      /**
       * Background Position
       * @see https://tailwindcss.com/docs/background-position
       */
      "bg-position": [{
        bg: scaleBgPosition()
      }],
      /**
       * Background Repeat
       * @see https://tailwindcss.com/docs/background-repeat
       */
      "bg-repeat": [{
        bg: scaleBgRepeat()
      }],
      /**
       * Background Size
       * @see https://tailwindcss.com/docs/background-size
       */
      "bg-size": [{
        bg: scaleBgSize()
      }],
      /**
       * Background Image
       * @see https://tailwindcss.com/docs/background-image
       */
      "bg-image": [{
        bg: ["none", {
          linear: [{
            to: ["t", "tr", "r", "br", "b", "bl", "l", "tl"]
          }, isInteger, isArbitraryVariable, isArbitraryValue],
          radial: ["", isArbitraryVariable, isArbitraryValue],
          conic: [isInteger, isArbitraryVariable, isArbitraryValue]
        }, isArbitraryVariableImage, isArbitraryImage]
      }],
      /**
       * Background Color
       * @see https://tailwindcss.com/docs/background-color
       */
      "bg-color": [{
        bg: scaleColor()
      }],
      /**
       * Gradient Color Stops From Position
       * @see https://tailwindcss.com/docs/gradient-color-stops
       */
      "gradient-from-pos": [{
        from: scaleGradientStopPosition()
      }],
      /**
       * Gradient Color Stops Via Position
       * @see https://tailwindcss.com/docs/gradient-color-stops
       */
      "gradient-via-pos": [{
        via: scaleGradientStopPosition()
      }],
      /**
       * Gradient Color Stops To Position
       * @see https://tailwindcss.com/docs/gradient-color-stops
       */
      "gradient-to-pos": [{
        to: scaleGradientStopPosition()
      }],
      /**
       * Gradient Color Stops From
       * @see https://tailwindcss.com/docs/gradient-color-stops
       */
      "gradient-from": [{
        from: scaleColor()
      }],
      /**
       * Gradient Color Stops Via
       * @see https://tailwindcss.com/docs/gradient-color-stops
       */
      "gradient-via": [{
        via: scaleColor()
      }],
      /**
       * Gradient Color Stops To
       * @see https://tailwindcss.com/docs/gradient-color-stops
       */
      "gradient-to": [{
        to: scaleColor()
      }],
      // ---------------
      // --- Borders ---
      // ---------------
      /**
       * Border Radius
       * @see https://tailwindcss.com/docs/border-radius
       */
      rounded: [{
        rounded: scaleRadius()
      }],
      /**
       * Border Radius Start
       * @see https://tailwindcss.com/docs/border-radius
       */
      "rounded-s": [{
        "rounded-s": scaleRadius()
      }],
      /**
       * Border Radius End
       * @see https://tailwindcss.com/docs/border-radius
       */
      "rounded-e": [{
        "rounded-e": scaleRadius()
      }],
      /**
       * Border Radius Top
       * @see https://tailwindcss.com/docs/border-radius
       */
      "rounded-t": [{
        "rounded-t": scaleRadius()
      }],
      /**
       * Border Radius Right
       * @see https://tailwindcss.com/docs/border-radius
       */
      "rounded-r": [{
        "rounded-r": scaleRadius()
      }],
      /**
       * Border Radius Bottom
       * @see https://tailwindcss.com/docs/border-radius
       */
      "rounded-b": [{
        "rounded-b": scaleRadius()
      }],
      /**
       * Border Radius Left
       * @see https://tailwindcss.com/docs/border-radius
       */
      "rounded-l": [{
        "rounded-l": scaleRadius()
      }],
      /**
       * Border Radius Start Start
       * @see https://tailwindcss.com/docs/border-radius
       */
      "rounded-ss": [{
        "rounded-ss": scaleRadius()
      }],
      /**
       * Border Radius Start End
       * @see https://tailwindcss.com/docs/border-radius
       */
      "rounded-se": [{
        "rounded-se": scaleRadius()
      }],
      /**
       * Border Radius End End
       * @see https://tailwindcss.com/docs/border-radius
       */
      "rounded-ee": [{
        "rounded-ee": scaleRadius()
      }],
      /**
       * Border Radius End Start
       * @see https://tailwindcss.com/docs/border-radius
       */
      "rounded-es": [{
        "rounded-es": scaleRadius()
      }],
      /**
       * Border Radius Top Left
       * @see https://tailwindcss.com/docs/border-radius
       */
      "rounded-tl": [{
        "rounded-tl": scaleRadius()
      }],
      /**
       * Border Radius Top Right
       * @see https://tailwindcss.com/docs/border-radius
       */
      "rounded-tr": [{
        "rounded-tr": scaleRadius()
      }],
      /**
       * Border Radius Bottom Right
       * @see https://tailwindcss.com/docs/border-radius
       */
      "rounded-br": [{
        "rounded-br": scaleRadius()
      }],
      /**
       * Border Radius Bottom Left
       * @see https://tailwindcss.com/docs/border-radius
       */
      "rounded-bl": [{
        "rounded-bl": scaleRadius()
      }],
      /**
       * Border Width
       * @see https://tailwindcss.com/docs/border-width
       */
      "border-w": [{
        border: scaleBorderWidth()
      }],
      /**
       * Border Width Inline
       * @see https://tailwindcss.com/docs/border-width
       */
      "border-w-x": [{
        "border-x": scaleBorderWidth()
      }],
      /**
       * Border Width Block
       * @see https://tailwindcss.com/docs/border-width
       */
      "border-w-y": [{
        "border-y": scaleBorderWidth()
      }],
      /**
       * Border Width Inline Start
       * @see https://tailwindcss.com/docs/border-width
       */
      "border-w-s": [{
        "border-s": scaleBorderWidth()
      }],
      /**
       * Border Width Inline End
       * @see https://tailwindcss.com/docs/border-width
       */
      "border-w-e": [{
        "border-e": scaleBorderWidth()
      }],
      /**
       * Border Width Block Start
       * @see https://tailwindcss.com/docs/border-width
       */
      "border-w-bs": [{
        "border-bs": scaleBorderWidth()
      }],
      /**
       * Border Width Block End
       * @see https://tailwindcss.com/docs/border-width
       */
      "border-w-be": [{
        "border-be": scaleBorderWidth()
      }],
      /**
       * Border Width Top
       * @see https://tailwindcss.com/docs/border-width
       */
      "border-w-t": [{
        "border-t": scaleBorderWidth()
      }],
      /**
       * Border Width Right
       * @see https://tailwindcss.com/docs/border-width
       */
      "border-w-r": [{
        "border-r": scaleBorderWidth()
      }],
      /**
       * Border Width Bottom
       * @see https://tailwindcss.com/docs/border-width
       */
      "border-w-b": [{
        "border-b": scaleBorderWidth()
      }],
      /**
       * Border Width Left
       * @see https://tailwindcss.com/docs/border-width
       */
      "border-w-l": [{
        "border-l": scaleBorderWidth()
      }],
      /**
       * Divide Width X
       * @see https://tailwindcss.com/docs/border-width#between-children
       */
      "divide-x": [{
        "divide-x": scaleBorderWidth()
      }],
      /**
       * Divide Width X Reverse
       * @see https://tailwindcss.com/docs/border-width#between-children
       */
      "divide-x-reverse": ["divide-x-reverse"],
      /**
       * Divide Width Y
       * @see https://tailwindcss.com/docs/border-width#between-children
       */
      "divide-y": [{
        "divide-y": scaleBorderWidth()
      }],
      /**
       * Divide Width Y Reverse
       * @see https://tailwindcss.com/docs/border-width#between-children
       */
      "divide-y-reverse": ["divide-y-reverse"],
      /**
       * Border Style
       * @see https://tailwindcss.com/docs/border-style
       */
      "border-style": [{
        border: [...scaleLineStyle(), "hidden", "none"]
      }],
      /**
       * Divide Style
       * @see https://tailwindcss.com/docs/border-style#setting-the-divider-style
       */
      "divide-style": [{
        divide: [...scaleLineStyle(), "hidden", "none"]
      }],
      /**
       * Border Color
       * @see https://tailwindcss.com/docs/border-color
       */
      "border-color": [{
        border: scaleColor()
      }],
      /**
       * Border Color Inline
       * @see https://tailwindcss.com/docs/border-color
       */
      "border-color-x": [{
        "border-x": scaleColor()
      }],
      /**
       * Border Color Block
       * @see https://tailwindcss.com/docs/border-color
       */
      "border-color-y": [{
        "border-y": scaleColor()
      }],
      /**
       * Border Color Inline Start
       * @see https://tailwindcss.com/docs/border-color
       */
      "border-color-s": [{
        "border-s": scaleColor()
      }],
      /**
       * Border Color Inline End
       * @see https://tailwindcss.com/docs/border-color
       */
      "border-color-e": [{
        "border-e": scaleColor()
      }],
      /**
       * Border Color Block Start
       * @see https://tailwindcss.com/docs/border-color
       */
      "border-color-bs": [{
        "border-bs": scaleColor()
      }],
      /**
       * Border Color Block End
       * @see https://tailwindcss.com/docs/border-color
       */
      "border-color-be": [{
        "border-be": scaleColor()
      }],
      /**
       * Border Color Top
       * @see https://tailwindcss.com/docs/border-color
       */
      "border-color-t": [{
        "border-t": scaleColor()
      }],
      /**
       * Border Color Right
       * @see https://tailwindcss.com/docs/border-color
       */
      "border-color-r": [{
        "border-r": scaleColor()
      }],
      /**
       * Border Color Bottom
       * @see https://tailwindcss.com/docs/border-color
       */
      "border-color-b": [{
        "border-b": scaleColor()
      }],
      /**
       * Border Color Left
       * @see https://tailwindcss.com/docs/border-color
       */
      "border-color-l": [{
        "border-l": scaleColor()
      }],
      /**
       * Divide Color
       * @see https://tailwindcss.com/docs/divide-color
       */
      "divide-color": [{
        divide: scaleColor()
      }],
      /**
       * Outline Style
       * @see https://tailwindcss.com/docs/outline-style
       */
      "outline-style": [{
        outline: [...scaleLineStyle(), "none", "hidden"]
      }],
      /**
       * Outline Offset
       * @see https://tailwindcss.com/docs/outline-offset
       */
      "outline-offset": [{
        "outline-offset": [isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Outline Width
       * @see https://tailwindcss.com/docs/outline-width
       */
      "outline-w": [{
        outline: ["", isNumber, isArbitraryVariableLength, isArbitraryLength]
      }],
      /**
       * Outline Color
       * @see https://tailwindcss.com/docs/outline-color
       */
      "outline-color": [{
        outline: scaleColor()
      }],
      // ---------------
      // --- Effects ---
      // ---------------
      /**
       * Box Shadow
       * @see https://tailwindcss.com/docs/box-shadow
       */
      shadow: [{
        shadow: [
          // Deprecated since Tailwind CSS v4.0.0
          "",
          "none",
          themeShadow,
          isArbitraryVariableShadow,
          isArbitraryShadow
        ]
      }],
      /**
       * Box Shadow Color
       * @see https://tailwindcss.com/docs/box-shadow#setting-the-shadow-color
       */
      "shadow-color": [{
        shadow: scaleColor()
      }],
      /**
       * Inset Box Shadow
       * @see https://tailwindcss.com/docs/box-shadow#adding-an-inset-shadow
       */
      "inset-shadow": [{
        "inset-shadow": ["none", themeInsetShadow, isArbitraryVariableShadow, isArbitraryShadow]
      }],
      /**
       * Inset Box Shadow Color
       * @see https://tailwindcss.com/docs/box-shadow#setting-the-inset-shadow-color
       */
      "inset-shadow-color": [{
        "inset-shadow": scaleColor()
      }],
      /**
       * Ring Width
       * @see https://tailwindcss.com/docs/box-shadow#adding-a-ring
       */
      "ring-w": [{
        ring: scaleBorderWidth()
      }],
      /**
       * Ring Width Inset
       * @see https://v3.tailwindcss.com/docs/ring-width#inset-rings
       * @deprecated since Tailwind CSS v4.0.0
       * @see https://github.com/tailwindlabs/tailwindcss/blob/v4.0.0/packages/tailwindcss/src/utilities.ts#L4158
       */
      "ring-w-inset": ["ring-inset"],
      /**
       * Ring Color
       * @see https://tailwindcss.com/docs/box-shadow#setting-the-ring-color
       */
      "ring-color": [{
        ring: scaleColor()
      }],
      /**
       * Ring Offset Width
       * @see https://v3.tailwindcss.com/docs/ring-offset-width
       * @deprecated since Tailwind CSS v4.0.0
       * @see https://github.com/tailwindlabs/tailwindcss/blob/v4.0.0/packages/tailwindcss/src/utilities.ts#L4158
       */
      "ring-offset-w": [{
        "ring-offset": [isNumber, isArbitraryLength]
      }],
      /**
       * Ring Offset Color
       * @see https://v3.tailwindcss.com/docs/ring-offset-color
       * @deprecated since Tailwind CSS v4.0.0
       * @see https://github.com/tailwindlabs/tailwindcss/blob/v4.0.0/packages/tailwindcss/src/utilities.ts#L4158
       */
      "ring-offset-color": [{
        "ring-offset": scaleColor()
      }],
      /**
       * Inset Ring Width
       * @see https://tailwindcss.com/docs/box-shadow#adding-an-inset-ring
       */
      "inset-ring-w": [{
        "inset-ring": scaleBorderWidth()
      }],
      /**
       * Inset Ring Color
       * @see https://tailwindcss.com/docs/box-shadow#setting-the-inset-ring-color
       */
      "inset-ring-color": [{
        "inset-ring": scaleColor()
      }],
      /**
       * Text Shadow
       * @see https://tailwindcss.com/docs/text-shadow
       */
      "text-shadow": [{
        "text-shadow": ["none", themeTextShadow, isArbitraryVariableShadow, isArbitraryShadow]
      }],
      /**
       * Text Shadow Color
       * @see https://tailwindcss.com/docs/text-shadow#setting-the-shadow-color
       */
      "text-shadow-color": [{
        "text-shadow": scaleColor()
      }],
      /**
       * Opacity
       * @see https://tailwindcss.com/docs/opacity
       */
      opacity: [{
        opacity: [isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Mix Blend Mode
       * @see https://tailwindcss.com/docs/mix-blend-mode
       */
      "mix-blend": [{
        "mix-blend": [...scaleBlendMode(), "plus-darker", "plus-lighter"]
      }],
      /**
       * Background Blend Mode
       * @see https://tailwindcss.com/docs/background-blend-mode
       */
      "bg-blend": [{
        "bg-blend": scaleBlendMode()
      }],
      /**
       * Mask Clip
       * @see https://tailwindcss.com/docs/mask-clip
       */
      "mask-clip": [{
        "mask-clip": ["border", "padding", "content", "fill", "stroke", "view"]
      }, "mask-no-clip"],
      /**
       * Mask Composite
       * @see https://tailwindcss.com/docs/mask-composite
       */
      "mask-composite": [{
        mask: ["add", "subtract", "intersect", "exclude"]
      }],
      /**
       * Mask Image
       * @see https://tailwindcss.com/docs/mask-image
       */
      "mask-image-linear-pos": [{
        "mask-linear": [isNumber]
      }],
      "mask-image-linear-from-pos": [{
        "mask-linear-from": scaleMaskImagePosition()
      }],
      "mask-image-linear-to-pos": [{
        "mask-linear-to": scaleMaskImagePosition()
      }],
      "mask-image-linear-from-color": [{
        "mask-linear-from": scaleColor()
      }],
      "mask-image-linear-to-color": [{
        "mask-linear-to": scaleColor()
      }],
      "mask-image-t-from-pos": [{
        "mask-t-from": scaleMaskImagePosition()
      }],
      "mask-image-t-to-pos": [{
        "mask-t-to": scaleMaskImagePosition()
      }],
      "mask-image-t-from-color": [{
        "mask-t-from": scaleColor()
      }],
      "mask-image-t-to-color": [{
        "mask-t-to": scaleColor()
      }],
      "mask-image-r-from-pos": [{
        "mask-r-from": scaleMaskImagePosition()
      }],
      "mask-image-r-to-pos": [{
        "mask-r-to": scaleMaskImagePosition()
      }],
      "mask-image-r-from-color": [{
        "mask-r-from": scaleColor()
      }],
      "mask-image-r-to-color": [{
        "mask-r-to": scaleColor()
      }],
      "mask-image-b-from-pos": [{
        "mask-b-from": scaleMaskImagePosition()
      }],
      "mask-image-b-to-pos": [{
        "mask-b-to": scaleMaskImagePosition()
      }],
      "mask-image-b-from-color": [{
        "mask-b-from": scaleColor()
      }],
      "mask-image-b-to-color": [{
        "mask-b-to": scaleColor()
      }],
      "mask-image-l-from-pos": [{
        "mask-l-from": scaleMaskImagePosition()
      }],
      "mask-image-l-to-pos": [{
        "mask-l-to": scaleMaskImagePosition()
      }],
      "mask-image-l-from-color": [{
        "mask-l-from": scaleColor()
      }],
      "mask-image-l-to-color": [{
        "mask-l-to": scaleColor()
      }],
      "mask-image-x-from-pos": [{
        "mask-x-from": scaleMaskImagePosition()
      }],
      "mask-image-x-to-pos": [{
        "mask-x-to": scaleMaskImagePosition()
      }],
      "mask-image-x-from-color": [{
        "mask-x-from": scaleColor()
      }],
      "mask-image-x-to-color": [{
        "mask-x-to": scaleColor()
      }],
      "mask-image-y-from-pos": [{
        "mask-y-from": scaleMaskImagePosition()
      }],
      "mask-image-y-to-pos": [{
        "mask-y-to": scaleMaskImagePosition()
      }],
      "mask-image-y-from-color": [{
        "mask-y-from": scaleColor()
      }],
      "mask-image-y-to-color": [{
        "mask-y-to": scaleColor()
      }],
      "mask-image-radial": [{
        "mask-radial": [isArbitraryVariable, isArbitraryValue]
      }],
      "mask-image-radial-from-pos": [{
        "mask-radial-from": scaleMaskImagePosition()
      }],
      "mask-image-radial-to-pos": [{
        "mask-radial-to": scaleMaskImagePosition()
      }],
      "mask-image-radial-from-color": [{
        "mask-radial-from": scaleColor()
      }],
      "mask-image-radial-to-color": [{
        "mask-radial-to": scaleColor()
      }],
      "mask-image-radial-shape": [{
        "mask-radial": ["circle", "ellipse"]
      }],
      "mask-image-radial-size": [{
        "mask-radial": [{
          closest: ["side", "corner"],
          farthest: ["side", "corner"]
        }]
      }],
      "mask-image-radial-pos": [{
        "mask-radial-at": scalePosition()
      }],
      "mask-image-conic-pos": [{
        "mask-conic": [isNumber]
      }],
      "mask-image-conic-from-pos": [{
        "mask-conic-from": scaleMaskImagePosition()
      }],
      "mask-image-conic-to-pos": [{
        "mask-conic-to": scaleMaskImagePosition()
      }],
      "mask-image-conic-from-color": [{
        "mask-conic-from": scaleColor()
      }],
      "mask-image-conic-to-color": [{
        "mask-conic-to": scaleColor()
      }],
      /**
       * Mask Mode
       * @see https://tailwindcss.com/docs/mask-mode
       */
      "mask-mode": [{
        mask: ["alpha", "luminance", "match"]
      }],
      /**
       * Mask Origin
       * @see https://tailwindcss.com/docs/mask-origin
       */
      "mask-origin": [{
        "mask-origin": ["border", "padding", "content", "fill", "stroke", "view"]
      }],
      /**
       * Mask Position
       * @see https://tailwindcss.com/docs/mask-position
       */
      "mask-position": [{
        mask: scaleBgPosition()
      }],
      /**
       * Mask Repeat
       * @see https://tailwindcss.com/docs/mask-repeat
       */
      "mask-repeat": [{
        mask: scaleBgRepeat()
      }],
      /**
       * Mask Size
       * @see https://tailwindcss.com/docs/mask-size
       */
      "mask-size": [{
        mask: scaleBgSize()
      }],
      /**
       * Mask Type
       * @see https://tailwindcss.com/docs/mask-type
       */
      "mask-type": [{
        "mask-type": ["alpha", "luminance"]
      }],
      /**
       * Mask Image
       * @see https://tailwindcss.com/docs/mask-image
       */
      "mask-image": [{
        mask: ["none", isArbitraryVariable, isArbitraryValue]
      }],
      // ---------------
      // --- Filters ---
      // ---------------
      /**
       * Filter
       * @see https://tailwindcss.com/docs/filter
       */
      filter: [{
        filter: [
          // Deprecated since Tailwind CSS v3.0.0
          "",
          "none",
          isArbitraryVariable,
          isArbitraryValue
        ]
      }],
      /**
       * Blur
       * @see https://tailwindcss.com/docs/blur
       */
      blur: [{
        blur: scaleBlur()
      }],
      /**
       * Brightness
       * @see https://tailwindcss.com/docs/brightness
       */
      brightness: [{
        brightness: [isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Contrast
       * @see https://tailwindcss.com/docs/contrast
       */
      contrast: [{
        contrast: [isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Drop Shadow
       * @see https://tailwindcss.com/docs/drop-shadow
       */
      "drop-shadow": [{
        "drop-shadow": [
          // Deprecated since Tailwind CSS v4.0.0
          "",
          "none",
          themeDropShadow,
          isArbitraryVariableShadow,
          isArbitraryShadow
        ]
      }],
      /**
       * Drop Shadow Color
       * @see https://tailwindcss.com/docs/filter-drop-shadow#setting-the-shadow-color
       */
      "drop-shadow-color": [{
        "drop-shadow": scaleColor()
      }],
      /**
       * Grayscale
       * @see https://tailwindcss.com/docs/grayscale
       */
      grayscale: [{
        grayscale: ["", isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Hue Rotate
       * @see https://tailwindcss.com/docs/hue-rotate
       */
      "hue-rotate": [{
        "hue-rotate": [isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Invert
       * @see https://tailwindcss.com/docs/invert
       */
      invert: [{
        invert: ["", isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Saturate
       * @see https://tailwindcss.com/docs/saturate
       */
      saturate: [{
        saturate: [isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Sepia
       * @see https://tailwindcss.com/docs/sepia
       */
      sepia: [{
        sepia: ["", isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Backdrop Filter
       * @see https://tailwindcss.com/docs/backdrop-filter
       */
      "backdrop-filter": [{
        "backdrop-filter": [
          // Deprecated since Tailwind CSS v3.0.0
          "",
          "none",
          isArbitraryVariable,
          isArbitraryValue
        ]
      }],
      /**
       * Backdrop Blur
       * @see https://tailwindcss.com/docs/backdrop-blur
       */
      "backdrop-blur": [{
        "backdrop-blur": scaleBlur()
      }],
      /**
       * Backdrop Brightness
       * @see https://tailwindcss.com/docs/backdrop-brightness
       */
      "backdrop-brightness": [{
        "backdrop-brightness": [isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Backdrop Contrast
       * @see https://tailwindcss.com/docs/backdrop-contrast
       */
      "backdrop-contrast": [{
        "backdrop-contrast": [isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Backdrop Grayscale
       * @see https://tailwindcss.com/docs/backdrop-grayscale
       */
      "backdrop-grayscale": [{
        "backdrop-grayscale": ["", isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Backdrop Hue Rotate
       * @see https://tailwindcss.com/docs/backdrop-hue-rotate
       */
      "backdrop-hue-rotate": [{
        "backdrop-hue-rotate": [isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Backdrop Invert
       * @see https://tailwindcss.com/docs/backdrop-invert
       */
      "backdrop-invert": [{
        "backdrop-invert": ["", isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Backdrop Opacity
       * @see https://tailwindcss.com/docs/backdrop-opacity
       */
      "backdrop-opacity": [{
        "backdrop-opacity": [isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Backdrop Saturate
       * @see https://tailwindcss.com/docs/backdrop-saturate
       */
      "backdrop-saturate": [{
        "backdrop-saturate": [isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Backdrop Sepia
       * @see https://tailwindcss.com/docs/backdrop-sepia
       */
      "backdrop-sepia": [{
        "backdrop-sepia": ["", isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      // --------------
      // --- Tables ---
      // --------------
      /**
       * Border Collapse
       * @see https://tailwindcss.com/docs/border-collapse
       */
      "border-collapse": [{
        border: ["collapse", "separate"]
      }],
      /**
       * Border Spacing
       * @see https://tailwindcss.com/docs/border-spacing
       */
      "border-spacing": [{
        "border-spacing": scaleUnambiguousSpacing()
      }],
      /**
       * Border Spacing X
       * @see https://tailwindcss.com/docs/border-spacing
       */
      "border-spacing-x": [{
        "border-spacing-x": scaleUnambiguousSpacing()
      }],
      /**
       * Border Spacing Y
       * @see https://tailwindcss.com/docs/border-spacing
       */
      "border-spacing-y": [{
        "border-spacing-y": scaleUnambiguousSpacing()
      }],
      /**
       * Table Layout
       * @see https://tailwindcss.com/docs/table-layout
       */
      "table-layout": [{
        table: ["auto", "fixed"]
      }],
      /**
       * Caption Side
       * @see https://tailwindcss.com/docs/caption-side
       */
      caption: [{
        caption: ["top", "bottom"]
      }],
      // ---------------------------------
      // --- Transitions and Animation ---
      // ---------------------------------
      /**
       * Transition Property
       * @see https://tailwindcss.com/docs/transition-property
       */
      transition: [{
        transition: ["", "all", "colors", "opacity", "shadow", "transform", "none", isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Transition Behavior
       * @see https://tailwindcss.com/docs/transition-behavior
       */
      "transition-behavior": [{
        transition: ["normal", "discrete"]
      }],
      /**
       * Transition Duration
       * @see https://tailwindcss.com/docs/transition-duration
       */
      duration: [{
        duration: [isNumber, "initial", isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Transition Timing Function
       * @see https://tailwindcss.com/docs/transition-timing-function
       */
      ease: [{
        ease: ["linear", "initial", themeEase, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Transition Delay
       * @see https://tailwindcss.com/docs/transition-delay
       */
      delay: [{
        delay: [isNumber, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Animation
       * @see https://tailwindcss.com/docs/animation
       */
      animate: [{
        animate: ["none", themeAnimate, isArbitraryVariable, isArbitraryValue]
      }],
      // ------------------
      // --- Transforms ---
      // ------------------
      /**
       * Backface Visibility
       * @see https://tailwindcss.com/docs/backface-visibility
       */
      backface: [{
        backface: ["hidden", "visible"]
      }],
      /**
       * Perspective
       * @see https://tailwindcss.com/docs/perspective
       */
      perspective: [{
        perspective: [themePerspective, isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Perspective Origin
       * @see https://tailwindcss.com/docs/perspective-origin
       */
      "perspective-origin": [{
        "perspective-origin": scalePositionWithArbitrary()
      }],
      /**
       * Rotate
       * @see https://tailwindcss.com/docs/rotate
       */
      rotate: [{
        rotate: scaleRotate()
      }],
      /**
       * Rotate X
       * @see https://tailwindcss.com/docs/rotate
       */
      "rotate-x": [{
        "rotate-x": scaleRotate()
      }],
      /**
       * Rotate Y
       * @see https://tailwindcss.com/docs/rotate
       */
      "rotate-y": [{
        "rotate-y": scaleRotate()
      }],
      /**
       * Rotate Z
       * @see https://tailwindcss.com/docs/rotate
       */
      "rotate-z": [{
        "rotate-z": scaleRotate()
      }],
      /**
       * Scale
       * @see https://tailwindcss.com/docs/scale
       */
      scale: [{
        scale: scaleScale()
      }],
      /**
       * Scale X
       * @see https://tailwindcss.com/docs/scale
       */
      "scale-x": [{
        "scale-x": scaleScale()
      }],
      /**
       * Scale Y
       * @see https://tailwindcss.com/docs/scale
       */
      "scale-y": [{
        "scale-y": scaleScale()
      }],
      /**
       * Scale Z
       * @see https://tailwindcss.com/docs/scale
       */
      "scale-z": [{
        "scale-z": scaleScale()
      }],
      /**
       * Scale 3D
       * @see https://tailwindcss.com/docs/scale
       */
      "scale-3d": ["scale-3d"],
      /**
       * Skew
       * @see https://tailwindcss.com/docs/skew
       */
      skew: [{
        skew: scaleSkew()
      }],
      /**
       * Skew X
       * @see https://tailwindcss.com/docs/skew
       */
      "skew-x": [{
        "skew-x": scaleSkew()
      }],
      /**
       * Skew Y
       * @see https://tailwindcss.com/docs/skew
       */
      "skew-y": [{
        "skew-y": scaleSkew()
      }],
      /**
       * Transform
       * @see https://tailwindcss.com/docs/transform
       */
      transform: [{
        transform: [isArbitraryVariable, isArbitraryValue, "", "none", "gpu", "cpu"]
      }],
      /**
       * Transform Origin
       * @see https://tailwindcss.com/docs/transform-origin
       */
      "transform-origin": [{
        origin: scalePositionWithArbitrary()
      }],
      /**
       * Transform Style
       * @see https://tailwindcss.com/docs/transform-style
       */
      "transform-style": [{
        transform: ["3d", "flat"]
      }],
      /**
       * Translate
       * @see https://tailwindcss.com/docs/translate
       */
      translate: [{
        translate: scaleTranslate()
      }],
      /**
       * Translate X
       * @see https://tailwindcss.com/docs/translate
       */
      "translate-x": [{
        "translate-x": scaleTranslate()
      }],
      /**
       * Translate Y
       * @see https://tailwindcss.com/docs/translate
       */
      "translate-y": [{
        "translate-y": scaleTranslate()
      }],
      /**
       * Translate Z
       * @see https://tailwindcss.com/docs/translate
       */
      "translate-z": [{
        "translate-z": scaleTranslate()
      }],
      /**
       * Translate None
       * @see https://tailwindcss.com/docs/translate
       */
      "translate-none": ["translate-none"],
      // ---------------------
      // --- Interactivity ---
      // ---------------------
      /**
       * Accent Color
       * @see https://tailwindcss.com/docs/accent-color
       */
      accent: [{
        accent: scaleColor()
      }],
      /**
       * Appearance
       * @see https://tailwindcss.com/docs/appearance
       */
      appearance: [{
        appearance: ["none", "auto"]
      }],
      /**
       * Caret Color
       * @see https://tailwindcss.com/docs/just-in-time-mode#caret-color-utilities
       */
      "caret-color": [{
        caret: scaleColor()
      }],
      /**
       * Color Scheme
       * @see https://tailwindcss.com/docs/color-scheme
       */
      "color-scheme": [{
        scheme: ["normal", "dark", "light", "light-dark", "only-dark", "only-light"]
      }],
      /**
       * Cursor
       * @see https://tailwindcss.com/docs/cursor
       */
      cursor: [{
        cursor: ["auto", "default", "pointer", "wait", "text", "move", "help", "not-allowed", "none", "context-menu", "progress", "cell", "crosshair", "vertical-text", "alias", "copy", "no-drop", "grab", "grabbing", "all-scroll", "col-resize", "row-resize", "n-resize", "e-resize", "s-resize", "w-resize", "ne-resize", "nw-resize", "se-resize", "sw-resize", "ew-resize", "ns-resize", "nesw-resize", "nwse-resize", "zoom-in", "zoom-out", isArbitraryVariable, isArbitraryValue]
      }],
      /**
       * Field Sizing
       * @see https://tailwindcss.com/docs/field-sizing
       */
      "field-sizing": [{
        "field-sizing": ["fixed", "content"]
      }],
      /**
       * Pointer Events
       * @see https://tailwindcss.com/docs/pointer-events
       */
      "pointer-events": [{
        "pointer-events": ["auto", "none"]
      }],
      /**
       * Resize
       * @see https://tailwindcss.com/docs/resize
       */
      resize: [{
        resize: ["none", "", "y", "x"]
      }],
      /**
       * Scroll Behavior
       * @see https://tailwindcss.com/docs/scroll-behavior
       */
      "scroll-behavior": [{
        scroll: ["auto", "smooth"]
      }],
      /**
       * Scroll Margin
       * @see https://tailwindcss.com/docs/scroll-margin
       */
      "scroll-m": [{
        "scroll-m": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Margin Inline
       * @see https://tailwindcss.com/docs/scroll-margin
       */
      "scroll-mx": [{
        "scroll-mx": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Margin Block
       * @see https://tailwindcss.com/docs/scroll-margin
       */
      "scroll-my": [{
        "scroll-my": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Margin Inline Start
       * @see https://tailwindcss.com/docs/scroll-margin
       */
      "scroll-ms": [{
        "scroll-ms": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Margin Inline End
       * @see https://tailwindcss.com/docs/scroll-margin
       */
      "scroll-me": [{
        "scroll-me": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Margin Block Start
       * @see https://tailwindcss.com/docs/scroll-margin
       */
      "scroll-mbs": [{
        "scroll-mbs": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Margin Block End
       * @see https://tailwindcss.com/docs/scroll-margin
       */
      "scroll-mbe": [{
        "scroll-mbe": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Margin Top
       * @see https://tailwindcss.com/docs/scroll-margin
       */
      "scroll-mt": [{
        "scroll-mt": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Margin Right
       * @see https://tailwindcss.com/docs/scroll-margin
       */
      "scroll-mr": [{
        "scroll-mr": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Margin Bottom
       * @see https://tailwindcss.com/docs/scroll-margin
       */
      "scroll-mb": [{
        "scroll-mb": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Margin Left
       * @see https://tailwindcss.com/docs/scroll-margin
       */
      "scroll-ml": [{
        "scroll-ml": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Padding
       * @see https://tailwindcss.com/docs/scroll-padding
       */
      "scroll-p": [{
        "scroll-p": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Padding Inline
       * @see https://tailwindcss.com/docs/scroll-padding
       */
      "scroll-px": [{
        "scroll-px": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Padding Block
       * @see https://tailwindcss.com/docs/scroll-padding
       */
      "scroll-py": [{
        "scroll-py": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Padding Inline Start
       * @see https://tailwindcss.com/docs/scroll-padding
       */
      "scroll-ps": [{
        "scroll-ps": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Padding Inline End
       * @see https://tailwindcss.com/docs/scroll-padding
       */
      "scroll-pe": [{
        "scroll-pe": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Padding Block Start
       * @see https://tailwindcss.com/docs/scroll-padding
       */
      "scroll-pbs": [{
        "scroll-pbs": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Padding Block End
       * @see https://tailwindcss.com/docs/scroll-padding
       */
      "scroll-pbe": [{
        "scroll-pbe": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Padding Top
       * @see https://tailwindcss.com/docs/scroll-padding
       */
      "scroll-pt": [{
        "scroll-pt": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Padding Right
       * @see https://tailwindcss.com/docs/scroll-padding
       */
      "scroll-pr": [{
        "scroll-pr": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Padding Bottom
       * @see https://tailwindcss.com/docs/scroll-padding
       */
      "scroll-pb": [{
        "scroll-pb": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Padding Left
       * @see https://tailwindcss.com/docs/scroll-padding
       */
      "scroll-pl": [{
        "scroll-pl": scaleUnambiguousSpacing()
      }],
      /**
       * Scroll Snap Align
       * @see https://tailwindcss.com/docs/scroll-snap-align
       */
      "snap-align": [{
        snap: ["start", "end", "center", "align-none"]
      }],
      /**
       * Scroll Snap Stop
       * @see https://tailwindcss.com/docs/scroll-snap-stop
       */
      "snap-stop": [{
        snap: ["normal", "always"]
      }],
      /**
       * Scroll Snap Type
       * @see https://tailwindcss.com/docs/scroll-snap-type
       */
      "snap-type": [{
        snap: ["none", "x", "y", "both"]
      }],
      /**
       * Scroll Snap Type Strictness
       * @see https://tailwindcss.com/docs/scroll-snap-type
       */
      "snap-strictness": [{
        snap: ["mandatory", "proximity"]
      }],
      /**
       * Touch Action
       * @see https://tailwindcss.com/docs/touch-action
       */
      touch: [{
        touch: ["auto", "none", "manipulation"]
      }],
      /**
       * Touch Action X
       * @see https://tailwindcss.com/docs/touch-action
       */
      "touch-x": [{
        "touch-pan": ["x", "left", "right"]
      }],
      /**
       * Touch Action Y
       * @see https://tailwindcss.com/docs/touch-action
       */
      "touch-y": [{
        "touch-pan": ["y", "up", "down"]
      }],
      /**
       * Touch Action Pinch Zoom
       * @see https://tailwindcss.com/docs/touch-action
       */
      "touch-pz": ["touch-pinch-zoom"],
      /**
       * User Select
       * @see https://tailwindcss.com/docs/user-select
       */
      select: [{
        select: ["none", "text", "all", "auto"]
      }],
      /**
       * Will Change
       * @see https://tailwindcss.com/docs/will-change
       */
      "will-change": [{
        "will-change": ["auto", "scroll", "contents", "transform", isArbitraryVariable, isArbitraryValue]
      }],
      // -----------
      // --- SVG ---
      // -----------
      /**
       * Fill
       * @see https://tailwindcss.com/docs/fill
       */
      fill: [{
        fill: ["none", ...scaleColor()]
      }],
      /**
       * Stroke Width
       * @see https://tailwindcss.com/docs/stroke-width
       */
      "stroke-w": [{
        stroke: [isNumber, isArbitraryVariableLength, isArbitraryLength, isArbitraryNumber]
      }],
      /**
       * Stroke
       * @see https://tailwindcss.com/docs/stroke
       */
      stroke: [{
        stroke: ["none", ...scaleColor()]
      }],
      // ---------------------
      // --- Accessibility ---
      // ---------------------
      /**
       * Forced Color Adjust
       * @see https://tailwindcss.com/docs/forced-color-adjust
       */
      "forced-color-adjust": [{
        "forced-color-adjust": ["auto", "none"]
      }]
    },
    conflictingClassGroups: {
      overflow: ["overflow-x", "overflow-y"],
      overscroll: ["overscroll-x", "overscroll-y"],
      inset: ["inset-x", "inset-y", "inset-bs", "inset-be", "start", "end", "top", "right", "bottom", "left"],
      "inset-x": ["right", "left"],
      "inset-y": ["top", "bottom"],
      flex: ["basis", "grow", "shrink"],
      gap: ["gap-x", "gap-y"],
      p: ["px", "py", "ps", "pe", "pbs", "pbe", "pt", "pr", "pb", "pl"],
      px: ["pr", "pl"],
      py: ["pt", "pb"],
      m: ["mx", "my", "ms", "me", "mbs", "mbe", "mt", "mr", "mb", "ml"],
      mx: ["mr", "ml"],
      my: ["mt", "mb"],
      size: ["w", "h"],
      "font-size": ["leading"],
      "fvn-normal": ["fvn-ordinal", "fvn-slashed-zero", "fvn-figure", "fvn-spacing", "fvn-fraction"],
      "fvn-ordinal": ["fvn-normal"],
      "fvn-slashed-zero": ["fvn-normal"],
      "fvn-figure": ["fvn-normal"],
      "fvn-spacing": ["fvn-normal"],
      "fvn-fraction": ["fvn-normal"],
      "line-clamp": ["display", "overflow"],
      rounded: ["rounded-s", "rounded-e", "rounded-t", "rounded-r", "rounded-b", "rounded-l", "rounded-ss", "rounded-se", "rounded-ee", "rounded-es", "rounded-tl", "rounded-tr", "rounded-br", "rounded-bl"],
      "rounded-s": ["rounded-ss", "rounded-es"],
      "rounded-e": ["rounded-se", "rounded-ee"],
      "rounded-t": ["rounded-tl", "rounded-tr"],
      "rounded-r": ["rounded-tr", "rounded-br"],
      "rounded-b": ["rounded-br", "rounded-bl"],
      "rounded-l": ["rounded-tl", "rounded-bl"],
      "border-spacing": ["border-spacing-x", "border-spacing-y"],
      "border-w": ["border-w-x", "border-w-y", "border-w-s", "border-w-e", "border-w-bs", "border-w-be", "border-w-t", "border-w-r", "border-w-b", "border-w-l"],
      "border-w-x": ["border-w-r", "border-w-l"],
      "border-w-y": ["border-w-t", "border-w-b"],
      "border-color": ["border-color-x", "border-color-y", "border-color-s", "border-color-e", "border-color-bs", "border-color-be", "border-color-t", "border-color-r", "border-color-b", "border-color-l"],
      "border-color-x": ["border-color-r", "border-color-l"],
      "border-color-y": ["border-color-t", "border-color-b"],
      translate: ["translate-x", "translate-y", "translate-none"],
      "translate-none": ["translate", "translate-x", "translate-y", "translate-z"],
      "scroll-m": ["scroll-mx", "scroll-my", "scroll-ms", "scroll-me", "scroll-mbs", "scroll-mbe", "scroll-mt", "scroll-mr", "scroll-mb", "scroll-ml"],
      "scroll-mx": ["scroll-mr", "scroll-ml"],
      "scroll-my": ["scroll-mt", "scroll-mb"],
      "scroll-p": ["scroll-px", "scroll-py", "scroll-ps", "scroll-pe", "scroll-pbs", "scroll-pbe", "scroll-pt", "scroll-pr", "scroll-pb", "scroll-pl"],
      "scroll-px": ["scroll-pr", "scroll-pl"],
      "scroll-py": ["scroll-pt", "scroll-pb"],
      touch: ["touch-x", "touch-y", "touch-pz"],
      "touch-x": ["touch"],
      "touch-y": ["touch"],
      "touch-pz": ["touch"]
    },
    conflictingClassGroupModifiers: {
      "font-size": ["leading"]
    },
    orderSensitiveModifiers: ["*", "**", "after", "backdrop", "before", "details-content", "file", "first-letter", "first-line", "marker", "placeholder", "selection"]
  };
};
var twMerge = /* @__PURE__ */ createTailwindMerge(getDefaultConfig);

// packages/ui/src/lib/utils.ts
function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// packages/ui/src/components/button.tsx
import { jsx } from "react/jsx-runtime";
var buttonVariants = cva(
  "inlineFlex itemsCenter justifyCenter gap2 rounded-[var(-RadiusMd)] fontMedium transitionColors duration-[var(-DurationNormal)] focusVisible:outlineNone focusVisible:ring2 focusVisible:ring-[var(-Accent)] focusVisible:ringOffset2 disabled:pointerEventsNone disabled:opacity50",
  {
    variants: {
      variant: {
        default: "bg-[var(-Accent)] text-[var(-AccentText)] hover:bg-[var(-AccentHover)]",
        secondary: "bg-[var(-BgTertiary)] text-[var(-TextPrimary)] hover:bg-[var(-BgSecondary)]",
        ghost: "hover:bg-[var(-BgTertiary)] text-[var(-TextSecondary)]",
        danger: "bg-[var(-ColorDanger500)] textWhite hover:bg-[var(-ColorDanger600)]"
      },
      size: {
        sm: "h8 px3 text-[var(-FontSizeSm)]",
        md: "h10 px4 text-[var(-FontSizeBase)]",
        lg: "h12 px6 text-[var(-FontSizeLg)]"
      }
    },
    defaultVariants: { variant: "default", size: "md" }
  }
);
var Button = React.forwardRef(
  ({ className, variant, size, ...props }, ref) => /* @__PURE__ */ jsx("button", { className: cn(buttonVariants({ variant, size, className })), ref, ...props })
);
Button.displayName = "Button";

// packages/ui/src/components/input.tsx
import * as React2 from "react";
import { jsx as jsx2, jsxs } from "react/jsx-runtime";
var Input = React2.forwardRef(
  ({ className, label, error, icon, id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
    return /* @__PURE__ */ jsxs("div", { className: "flex flexCol gap-[var(-Spacing1)]", children: [
      label && /* @__PURE__ */ jsx2("label", { htmlFor: inputId, className: "text-[var(-FontSizeSm)] fontMedium text-[var(-TextPrimary)]", children: label }),
      /* @__PURE__ */ jsxs("div", { className: "relative", children: [
        icon && /* @__PURE__ */ jsx2("span", { className: "absolute left3 top1/2 TranslateY1/2 text-[var(-TextTertiary)]", children: icon }),
        /* @__PURE__ */ jsx2(
          "input",
          {
            id: inputId,
            className: cn(
              "flex h10 wFull rounded-[var(-RadiusMd)] border border-[var(-BorderDefault)] bg-[var(-BgPrimary)] px3 py2 text-[var(-FontSizeBase)] text-[var(-TextPrimary)] placeholder:text-[var(-TextTertiary)] transitionColors duration-[var(-DurationFast)] focusVisible:outlineNone focusVisible:ring2 focusVisible:ring-[var(-Accent)] disabled:cursorNotAllowed disabled:opacity50",
              icon && "pl10",
              error && "border-[var(-ColorDanger500)] focusVisible:ring-[var(-ColorDanger500)]",
              className
            ),
            ref,
            ...props
          }
        )
      ] }),
      error && /* @__PURE__ */ jsx2("p", { className: "text-[var(-FontSizeSm)] text-[var(-ColorDanger500)]", children: error })
    ] });
  }
);
Input.displayName = "Input";

// packages/ui/src/components/card.tsx
import * as React3 from "react";
import { jsx as jsx3 } from "react/jsx-runtime";
var cardVariants = cva(
  "rounded-[var(-RadiusLg)] transitionShadow duration-[var(-DurationNormal)]",
  {
    variants: {
      variant: {
        default: "bg-[var(-BgPrimary)] border border-[var(-BorderDefault)]",
        elevated: "bg-[var(-BgPrimary)] shadow-[var(-ShadowMd)]",
        bordered: "bg-[var(-BgPrimary)] border2 border-[var(-BorderStrong)]"
      }
    },
    defaultVariants: { variant: "default" }
  }
);
var Card = React3.forwardRef(
  ({ className, variant, ...props }, ref) => /* @__PURE__ */ jsx3("div", { className: cn(cardVariants({ variant, className })), ref, ...props })
);
Card.displayName = "Card";
var CardHeader = React3.forwardRef(
  ({ className, ...props }, ref) => /* @__PURE__ */ jsx3("div", { className: cn("flex flexCol gap-[var(-Spacing1)] p-[var(-Spacing6)]", className), ref, ...props })
);
CardHeader.displayName = "CardHeader";
var CardContent = React3.forwardRef(
  ({ className, ...props }, ref) => /* @__PURE__ */ jsx3("div", { className: cn("px-[var(-Spacing6)] pb-[var(-Spacing6)]", className), ref, ...props })
);
CardContent.displayName = "CardContent";
var CardFooter = React3.forwardRef(
  ({ className, ...props }, ref) => /* @__PURE__ */ jsx3("div", { className: cn("flex itemsCenter px-[var(-Spacing6)] pb-[var(-Spacing6)]", className), ref, ...props })
);
CardFooter.displayName = "CardFooter";

// packages/ui/src/components/badge.tsx
import * as React4 from "react";
import { jsx as jsx4 } from "react/jsx-runtime";
var badgeVariants = cva(
  "inlineFlex itemsCenter rounded-[var(-RadiusFull)] px2.5 py0.5 text-[var(-FontSizeXs)] fontMedium transitionColors duration-[var(-DurationFast)]",
  {
    variants: {
      variant: {
        idle: "bg-[var(-BgTertiary)] text-[var(-TextSecondary)]",
        running: "bg-[var(-ColorInfo500)]/15 text-[var(-ColorInfo500)]",
        success: "bg-[var(-ColorSuccess500)]/15 text-[var(-ColorSuccess500)]",
        failed: "bg-[var(-ColorDanger500)]/15 text-[var(-ColorDanger500)]",
        warning: "bg-[var(-ColorWarning500)]/15 text-[var(-ColorWarning500)]",
        gain: "bg-[var(-ColorGain)]/15 text-[var(-ColorGain)]",
        loss: "bg-[var(-ColorLoss)]/15 text-[var(-ColorLoss)]"
      }
    },
    defaultVariants: { variant: "idle" }
  }
);
var Badge = React4.forwardRef(
  ({ className, variant, ...props }, ref) => /* @__PURE__ */ jsx4("span", { className: cn(badgeVariants({ variant, className })), ref, ...props })
);
Badge.displayName = "Badge";

// packages/ui/src/components/skeleton.tsx
import * as React5 from "react";
import { jsx as jsx5 } from "react/jsx-runtime";
var Skeleton = React5.forwardRef(
  ({ className, ...props }, ref) => /* @__PURE__ */ jsx5(
    "div",
    {
      className: cn(
        "animatePulse rounded-[var(-RadiusMd)] bg-[var(-BgTertiary)]",
        className
      ),
      ref,
      ...props
    }
  )
);
Skeleton.displayName = "Skeleton";

// packages/ui/src/components/kbd.tsx
import * as React6 from "react";
import { jsx as jsx6 } from "react/jsx-runtime";
var Kbd = React6.forwardRef(
  ({ className, ...props }, ref) => /* @__PURE__ */ jsx6(
    "kbd",
    {
      className: cn(
        "inlineFlex h5 itemsCenter justifyCenter rounded-[var(-RadiusSm)] border border-[var(-BorderStrong)] bg-[var(-BgSecondary)] px1.5 fontMono text-[0.625rem] fontMedium text-[var(-TextSecondary)] shadow-[var(-ShadowXs)]",
        className
      ),
      ref,
      ...props
    }
  )
);
Kbd.displayName = "Kbd";

// packages/ui/src/components/kpi-card.tsx
import * as React7 from "react";
import { jsx as jsx7, jsxs as jsxs2 } from "react/jsx-runtime";
var KpiCard = React7.forwardRef(
  ({ className, label, value, trend, trendValue, sparkline, ...props }, ref) => /* @__PURE__ */ jsxs2(
    "div",
    {
      className: cn(
        "flex flexCol gap-[var(-Spacing2)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-BgPrimary)] p-[var(-Spacing5)]",
        className
      ),
      ref,
      ...props,
      children: [
        /* @__PURE__ */ jsx7("span", { className: "text-[var(-FontSizeSm)] text-[var(-TextSecondary)]", children: label }),
        /* @__PURE__ */ jsxs2("div", { className: "flex itemsEnd justifyBetween gap-[var(-Spacing4)]", children: [
          /* @__PURE__ */ jsx7("span", { className: "fontMono text-[var(-FontSize3xl)] fontBold text-[var(-TextPrimary)] leadingNone", children: value }),
          sparkline && /* @__PURE__ */ jsx7("div", { className: "h8 w20", children: sparkline })
        ] }),
        trend && trendValue && /* @__PURE__ */ jsx7("div", { className: "flex itemsCenter gap1", children: /* @__PURE__ */ jsxs2(
          "span",
          {
            className: cn(
              "text-[var(-FontSizeSm)] fontMedium",
              trend === "up" && "text-[var(-ColorSuccess500)]",
              trend === "down" && "text-[var(-ColorDanger500)]",
              trend === "flat" && "text-[var(-TextTertiary)]"
            ),
            children: [
              trend === "up" ? "\u2191" : trend === "down" ? "\u2193" : "\u2192",
              " ",
              trendValue
            ]
          }
        ) })
      ]
    }
  )
);
KpiCard.displayName = "KpiCard";

// packages/ui/src/components/code-block.tsx
import * as React8 from "react";
import { jsx as jsx8, jsxs as jsxs3 } from "react/jsx-runtime";
var CodeBlock = React8.forwardRef(
  ({ className, code, language = "bash", showCopy = true, ...props }, ref) => {
    const [copied, setCopied] = React8.useState(false);
    const handleCopy = React8.useCallback(async () => {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2e3);
    }, [code]);
    return /* @__PURE__ */ jsxs3(
      "div",
      {
        className: cn(
          "relative rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-ColorNeutral950)]",
          className
        ),
        ref,
        ...props,
        children: [
          /* @__PURE__ */ jsxs3("div", { className: "flex itemsCenter justifyBetween borderB border-[var(-ColorNeutral800)] px4 py2", children: [
            /* @__PURE__ */ jsx8("span", { className: "text-[var(-FontSizeXs)] fontMedium text-[var(-ColorNeutral400)]", children: language }),
            showCopy && /* @__PURE__ */ jsx8(
              "button",
              {
                onClick: handleCopy,
                className: "text-[var(-FontSizeXs)] text-[var(-ColorNeutral400)] transitionColors duration-[var(-DurationFast)] hover:text-[var(-ColorNeutral200)]",
                children: copied ? "Copied!" : "Copy"
              }
            )
          ] }),
          /* @__PURE__ */ jsx8("pre", { className: "overflowXAuto p4", children: /* @__PURE__ */ jsx8("code", { className: "fontMono text-[var(-FontSizeSm)] text-[var(-ColorNeutral100)]", children: code }) })
        ]
      }
    );
  }
);
CodeBlock.displayName = "CodeBlock";

// packages/ui/src/components/credit-meter.tsx
import * as React9 from "react";
import { jsx as jsx9, jsxs as jsxs4 } from "react/jsx-runtime";
var CreditMeter = React9.forwardRef(
  ({ className, used, total, label, ...props }, ref) => {
    const percentage = Math.min(used / total * 100, 100);
    const circumference = 2 * Math.PI * 40;
    const strokeDashoffset = circumference - percentage / 100 * circumference;
    const color = percentage > 90 ? "var(-ColorDanger500)" : percentage > 70 ? "var(-ColorWarning500)" : "var(-Accent)";
    return /* @__PURE__ */ jsxs4("div", { className: cn("flex flexCol itemsCenter gap2", className), ref, ...props, children: [
      /* @__PURE__ */ jsxs4("svg", { width: "96", height: "96", viewBox: "0 0 96 96", className: "Rotate90", children: [
        /* @__PURE__ */ jsx9(
          "circle",
          {
            cx: "48",
            cy: "48",
            r: "40",
            fill: "none",
            stroke: "var(-BgTertiary)",
            strokeWidth: "6"
          }
        ),
        /* @__PURE__ */ jsx9(
          "circle",
          {
            cx: "48",
            cy: "48",
            r: "40",
            fill: "none",
            stroke: color,
            strokeWidth: "6",
            strokeLinecap: "round",
            strokeDasharray: circumference,
            strokeDashoffset,
            className: "transitionAll duration-[var(-DurationSlow)]"
          }
        )
      ] }),
      /* @__PURE__ */ jsxs4("div", { className: "absolute flex flexCol itemsCenter", children: [
        /* @__PURE__ */ jsx9("span", { className: "fontMono text-[var(-FontSizeLg)] fontBold text-[var(-TextPrimary)]", children: used }),
        /* @__PURE__ */ jsxs4("span", { className: "text-[var(-FontSizeXs)] text-[var(-TextTertiary)]", children: [
          "/ ",
          total
        ] })
      ] }),
      label && /* @__PURE__ */ jsx9("span", { className: "text-[var(-FontSizeSm)] text-[var(-TextSecondary)]", children: label })
    ] });
  }
);
CreditMeter.displayName = "CreditMeter";

// packages/ui/src/components/status-dot.tsx
import * as React10 from "react";
import { jsx as jsx10, jsxs as jsxs5 } from "react/jsx-runtime";
var statusDotVariants = cva(
  "relative inlineBlock h2.5 w2.5 roundedFull",
  {
    variants: {
      status: {
        online: "bg-[var(-ColorSuccess500)]",
        degraded: "bg-[var(-ColorWarning500)]",
        error: "bg-[var(-ColorDanger500)]",
        offline: "bg-[var(-ColorNeutral400)]"
      },
      pulse: {
        true: "",
        false: ""
      }
    },
    defaultVariants: { status: "offline", pulse: false }
  }
);
var StatusDot = React10.forwardRef(
  ({ className, status, pulse, ...props }, ref) => /* @__PURE__ */ jsxs5("span", { className: cn("relative inlineFlex", className), ref, ...props, children: [
    pulse && status !== "offline" && /* @__PURE__ */ jsx10(
      "span",
      {
        className: cn(
          "absolute inlineFlex hFull wFull animatePing roundedFull opacity75",
          status === "online" && "bg-[var(-ColorSuccess500)]",
          status === "degraded" && "bg-[var(-ColorWarning500)]",
          status === "error" && "bg-[var(-ColorDanger500)]"
        )
      }
    ),
    /* @__PURE__ */ jsx10("span", { className: cn(statusDotVariants({ status })) })
  ] })
);
StatusDot.displayName = "StatusDot";

// packages/ui/src/components/pipeline-badge.tsx
import * as React11 from "react";
import { jsx as jsx11, jsxs as jsxs6 } from "react/jsx-runtime";
var pipelineBadgeVariants = cva(
  "inlineFlex itemsCenter gap1.5 rounded-[var(-RadiusFull)] px3 py1 text-[var(-FontSizeXs)] fontSemibold uppercase trackingWider transitionAll duration-[var(-DurationNormal)]",
  {
    variants: {
      phase: {
        plan: "bg-[var(-ColorInfo500)]/15 text-[var(-ColorInfo500)]",
        execute: "bg-[var(-ColorWarning500)]/15 text-[var(-ColorWarning500)]",
        verify: "bg-[var(-ColorSuccess500)]/15 text-[var(-ColorSuccess500)]"
      },
      active: {
        true: "",
        false: "opacity50"
      }
    },
    defaultVariants: { phase: "plan", active: false }
  }
);
var PipelineBadge = React11.forwardRef(
  ({ className, phase, active, ...props }, ref) => /* @__PURE__ */ jsxs6("span", { className: cn(pipelineBadgeVariants({ phase, active, className })), ref, ...props, children: [
    active && /* @__PURE__ */ jsx11(
      "span",
      {
        className: cn(
          "h1.5 w1.5 animatePulse roundedFull",
          phase === "plan" && "bg-[var(-ColorInfo500)]",
          phase === "execute" && "bg-[var(-ColorWarning500)]",
          phase === "verify" && "bg-[var(-ColorSuccess500)]"
        )
      }
    ),
    phase
  ] })
);
PipelineBadge.displayName = "PipelineBadge";

// packages/ui/src/components/brand/mekong-logo.tsx
import * as React12 from "react";
import { jsx as jsx12, jsxs as jsxs7 } from "react/jsx-runtime";
var MekongLogo = React12.forwardRef(
  ({ className, size = 40, ...props }, ref) => /* @__PURE__ */ jsxs7(
    "svg",
    {
      width: size,
      height: size,
      viewBox: "0 0 48 48",
      fill: "none",
      className: cn("textCurrent", className),
      ref,
      ...props,
      children: [
        /* @__PURE__ */ jsx12(
          "path",
          {
            d: "M24 4 C24 4, 22 16, 14 24 C8 30, 4 36, 6 44",
            stroke: "currentColor",
            strokeWidth: "2.5",
            strokeLinecap: "round"
          }
        ),
        /* @__PURE__ */ jsx12(
          "path",
          {
            d: "M24 4 C24 4, 24 18, 24 28 C24 34, 24 38, 24 44",
            stroke: "currentColor",
            strokeWidth: "2.5",
            strokeLinecap: "round"
          }
        ),
        /* @__PURE__ */ jsx12(
          "path",
          {
            d: "M24 4 C24 4, 26 16, 34 24 C40 30, 44 36, 42 44",
            stroke: "currentColor",
            strokeWidth: "2.5",
            strokeLinecap: "round"
          }
        ),
        /* @__PURE__ */ jsx12(
          "path",
          {
            d: "M24 4 C24 4, 20 14, 10 20 C6 22, 2 28, 2 34",
            stroke: "currentColor",
            strokeWidth: "1.5",
            strokeLinecap: "round",
            opacity: "0.5"
          }
        ),
        /* @__PURE__ */ jsx12(
          "path",
          {
            d: "M24 4 C24 4, 28 14, 38 20 C42 22, 46 28, 46 34",
            stroke: "currentColor",
            strokeWidth: "1.5",
            strokeLinecap: "round",
            opacity: "0.5"
          }
        )
      ]
    }
  )
);
MekongLogo.displayName = "MekongLogo";

// packages/ui/src/components/brand/mekong-wordmark.tsx
import * as React13 from "react";
import { jsx as jsx13, jsxs as jsxs8 } from "react/jsx-runtime";
var MekongWordmark = React13.forwardRef(
  ({ className, showSubtitle = true, ...props }, ref) => /* @__PURE__ */ jsxs8("div", { className: cn("flex flexCol", className), ref, ...props, children: [
    /* @__PURE__ */ jsx13(
      "span",
      {
        className: "fontSans text-[var(-FontSize2xl)] fontBold tracking-[0.05em] text-[var(-TextPrimary)]",
        style: { fontWeight: 700 },
        children: "MEKONG"
      }
    ),
    showSubtitle && /* @__PURE__ */ jsx13(
      "span",
      {
        className: "text-[var(-FontSizeSm)] fontNormal trackingWide text-[var(-TextSecondary)]",
        style: { fontWeight: 400 },
        children: "Binh Ph\xE1p Venture Studio"
      }
    )
  ] })
);
MekongWordmark.displayName = "MekongWordmark";

// packages/ui/src/components/brand/loading-river.tsx
import * as React14 from "react";
import { jsx as jsx14, jsxs as jsxs9 } from "react/jsx-runtime";
var LoadingRiver = React14.forwardRef(
  ({ className, size = 48, ...props }, ref) => /* @__PURE__ */ jsxs9(
    "svg",
    {
      width: size,
      height: size,
      viewBox: "0 0 48 48",
      fill: "none",
      className: cn("text-[var(-Accent)]", className),
      ref,
      ...props,
      children: [
        /* @__PURE__ */ jsx14("style", { children: `
        @keyframes riverFlow {
          0% { strokeDashoffset: 80; }
          50% { strokeDashoffset: 0; }
          100% { strokeDashoffset: 80; }
        }
        .riverPath {
          strokeDasharray: 20 60;
          animation: riverFlow 2s easeInOut infinite;
        }
        .riverPathDelay1 { animationDelay: 0.4s; }
        .riverPathDelay2 { animationDelay: 0.8s; }
        @media (prefersReducedMotion: reduce) {
          .riverPath { animation: none; strokeDasharray: none; }
        }
      ` }),
        /* @__PURE__ */ jsx14(
          "path",
          {
            className: "riverPath",
            d: "M24 4 C22 14, 16 20, 10 28 C6 34, 6 38, 8 44",
            stroke: "currentColor",
            strokeWidth: "2",
            strokeLinecap: "round"
          }
        ),
        /* @__PURE__ */ jsx14(
          "path",
          {
            className: "riverPath riverPathDelay1",
            d: "M24 4 C24 14, 24 24, 24 34 C24 38, 24 40, 24 44",
            stroke: "currentColor",
            strokeWidth: "2",
            strokeLinecap: "round"
          }
        ),
        /* @__PURE__ */ jsx14(
          "path",
          {
            className: "riverPath riverPathDelay2",
            d: "M24 4 C26 14, 32 20, 38 28 C42 34, 42 38, 40 44",
            stroke: "currentColor",
            strokeWidth: "2",
            strokeLinecap: "round"
          }
        )
      ]
    }
  )
);
LoadingRiver.displayName = "LoadingRiver";

// packages/ui/src/components/brand/delta-pattern.tsx
import * as React15 from "react";
import { jsx as jsx15, jsxs as jsxs10 } from "react/jsx-runtime";
var DeltaPattern = React15.forwardRef(
  ({ className, variant = "horizontal", opacity = 0.04, ...props }, ref) => {
    if (variant === "radial") {
      return /* @__PURE__ */ jsx15(
        "svg",
        {
          className: cn("pointerEventsNone absolute inset0 hFull wFull text-[var(-Accent)]", className),
          viewBox: "0 0 400 400",
          fill: "none",
          ref,
          ...props,
          children: /* @__PURE__ */ jsx15("g", { stroke: "currentColor", strokeWidth: "0.5", opacity, children: Array.from({ length: 12 }, (_, i) => {
            const angle = i * 30 * Math.PI / 180;
            const cx2 = 200 + 60 * Math.cos(angle);
            const cy = 200 + 60 * Math.sin(angle);
            const ex = 200 + 180 * Math.cos(angle + 0.15);
            const ey = 200 + 180 * Math.sin(angle + 0.15);
            return /* @__PURE__ */ jsx15("path", { d: `M200,200 Q${cx2},${cy} ${ex},${ey}` }, i);
          }) })
        }
      );
    }
    return /* @__PURE__ */ jsx15(
      "svg",
      {
        className: cn("pointerEventsNone absolute inset0 hFull wFull text-[var(-Accent)]", className),
        viewBox: "0 0 800 120",
        fill: "none",
        preserveAspectRatio: "none",
        ref,
        ...props,
        children: /* @__PURE__ */ jsx15("g", { stroke: "currentColor", strokeWidth: "0.5", opacity, children: Array.from({ length: 8 }, (_, i) => {
          const startX = 100 * i + 50;
          return /* @__PURE__ */ jsxs10(React15.Fragment, { children: [
            /* @__PURE__ */ jsx15("path", { d: `M${startX},10 Q${startX - 20},40 ${startX - 40},60 Q${startX - 50},80 ${startX - 30},110` }),
            /* @__PURE__ */ jsx15("path", { d: `M${startX},10 Q${startX},35 ${startX},60 Q${startX},85 ${startX},110` }),
            /* @__PURE__ */ jsx15("path", { d: `M${startX},10 Q${startX + 20},40 ${startX + 40},60 Q${startX + 50},80 ${startX + 30},110` })
          ] }, i);
        }) })
      }
    );
  }
);
DeltaPattern.displayName = "DeltaPattern";

// packages/ui/src/components/dashboard/mission-card.tsx
import * as React16 from "react";
import { jsx as jsx16, jsxs as jsxs11 } from "react/jsx-runtime";
var statusStyles = {
  pending: "bg-[var(-BgTertiary)] text-[var(-TextSecondary)]",
  running: "bg-[var(-ColorInfo500)]/15 text-[var(-ColorInfo500)]",
  success: "bg-[var(-ColorSuccess500)]/15 text-[var(-ColorSuccess500)]",
  failed: "bg-[var(-ColorDanger500)]/15 text-[var(-ColorDanger500)]"
};
var MissionCard = React16.forwardRef(
  ({ className, title, status, creditCost, agents = [], expandable, children, ...props }, ref) => {
    const [expanded, setExpanded] = React16.useState(false);
    return /* @__PURE__ */ jsxs11(
      "div",
      {
        className: cn(
          "rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-BgPrimary)] transitionShadow duration-[var(-DurationNormal)]",
          status === "running" && "ring1 ring-[var(-ColorInfo500)]/30",
          className
        ),
        ref,
        ...props,
        children: [
          /* @__PURE__ */ jsxs11(
            "div",
            {
              className: cn("flex itemsCenter gap3 p-[var(-Spacing4)]", expandable && "cursorPointer"),
              onClick: expandable ? () => setExpanded(!expanded) : void 0,
              children: [
                /* @__PURE__ */ jsxs11("div", { className: "flex flex1 flexCol gap1", children: [
                  /* @__PURE__ */ jsx16("span", { className: "text-[var(-FontSizeSm)] fontMedium text-[var(-TextPrimary)]", children: title }),
                  /* @__PURE__ */ jsxs11("div", { className: "flex itemsCenter gap2", children: [
                    /* @__PURE__ */ jsx16("span", { className: cn(
                      "rounded-[var(-RadiusFull)] px2 py0.5 text-[0.625rem] fontSemibold uppercase",
                      statusStyles[status]
                    ), children: status }),
                    /* @__PURE__ */ jsxs11("span", { className: "fontMono text-[var(-FontSizeXs)] text-[var(-TextTertiary)]", children: [
                      creditCost,
                      " MCU"
                    ] })
                  ] })
                ] }),
                agents.length > 0 && /* @__PURE__ */ jsx16("div", { className: "flex SpaceX1", children: agents.map((agent) => /* @__PURE__ */ jsx16(
                  "span",
                  {
                    className: "flex h6 w6 itemsCenter justifyCenter roundedFull bg-[var(-Accent)] text-[0.625rem] fontBold text-[var(-AccentText)]",
                    title: agent,
                    children: agent[0]
                  },
                  agent
                )) }),
                expandable && /* @__PURE__ */ jsx16("span", { className: cn(
                  "text-[var(-TextTertiary)] transitionTransform duration-[var(-DurationFast)]",
                  expanded && "rotate180"
                ), children: "\u25BC" })
              ]
            }
          ),
          expandable && expanded && children && /* @__PURE__ */ jsx16("div", { className: "borderT border-[var(-BorderDefault)] p-[var(-Spacing4)]", children })
        ]
      }
    );
  }
);
MissionCard.displayName = "MissionCard";

// packages/ui/src/components/dashboard/pipeline-viz.tsx
import * as React17 from "react";
import { jsx as jsx17, jsxs as jsxs12 } from "react/jsx-runtime";
var stepConfig = {
  plan: { label: "Plan", color: "var(-ColorInfo500)", activeColor: "var(-ColorInfo500)" },
  execute: { label: "Execute", color: "var(-ColorWarning500)", activeColor: "var(-ColorWarning500)" },
  verify: { label: "Verify", color: "var(-ColorSuccess500)", activeColor: "var(-ColorSuccess500)" }
};
var stateStyles = {
  idle: "border-[var(-BorderDefault)] bg-[var(-BgSecondary)] text-[var(-TextTertiary)]",
  active: "ring2 ringOffset2 ringOffset-[var(-BgPrimary)]",
  done: "opacity100",
  failed: "border-[var(-ColorDanger500)] bg-[var(-ColorDanger500)]/10 text-[var(-ColorDanger500)]"
};
var PipelineViz = React17.forwardRef(
  ({ className, planState = "idle", executeState = "idle", verifyState = "idle", ...props }, ref) => {
    const steps = [
      { key: "plan", state: planState },
      { key: "execute", state: executeState },
      { key: "verify", state: verifyState }
    ];
    return /* @__PURE__ */ jsx17("div", { className: cn("flex itemsCenter gap2", className), ref, ...props, children: steps.map((step, i) => {
      const cfg = stepConfig[step.key];
      return /* @__PURE__ */ jsxs12(React17.Fragment, { children: [
        i > 0 && /* @__PURE__ */ jsx17("div", { className: cn(
          "h0.5 w8",
          step.state === "done" || step.state === "active" ? `bg-[${cfg.color}]` : "bg-[var(-BorderDefault)]"
        ) }),
        /* @__PURE__ */ jsxs12("div", { className: cn(
          "flex itemsCenter gap1.5 rounded-[var(-RadiusFull)] border px3 py1.5 text-[var(-FontSizeXs)] fontSemibold",
          stateStyles[step.state],
          step.state === "active" && `ring-[${cfg.activeColor}] border-[${cfg.color}] text-[${cfg.color}]`,
          step.state === "done" && `border-[${cfg.color}] bg-[${cfg.color}]/10 text-[${cfg.color}]`
        ), children: [
          step.state === "active" && /* @__PURE__ */ jsx17("span", { className: `h1.5 w1.5 animatePulse roundedFull bg-[${cfg.color}]` }),
          step.state === "done" && /* @__PURE__ */ jsx17("span", { children: "\u2713" }),
          step.state === "failed" && /* @__PURE__ */ jsx17("span", { children: "\u2717" }),
          cfg.label
        ] })
      ] }, step.key);
    }) });
  }
);
PipelineViz.displayName = "PipelineViz";

// packages/ui/src/components/dashboard/command-palette.tsx
import * as React18 from "react";
import { jsx as jsx18, jsxs as jsxs13 } from "react/jsx-runtime";
var CommandPalette = React18.forwardRef(
  ({ className, open, onOpenChange, commands, onSelect, placeholder = "Type a command...", ...props }, ref) => {
    const [query, setQuery] = React18.useState("");
    const inputRef = React18.useRef(null);
    const filtered = React18.useMemo(() => {
      if (!query) return commands;
      const q = query.toLowerCase();
      return commands.filter((c) => c.label.toLowerCase().includes(q));
    }, [commands, query]);
    const grouped = React18.useMemo(() => {
      const groups = {};
      for (const cmd of filtered) {
        const g = cmd.group ?? "Commands";
        (groups[g] ?? (groups[g] = [])).push(cmd);
      }
      return groups;
    }, [filtered]);
    React18.useEffect(() => {
      if (open) {
        setQuery("");
        setTimeout(() => inputRef.current?.focus(), 0);
      }
    }, [open]);
    React18.useEffect(() => {
      const handleKeyDown = (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === "k") {
          e.preventDefault();
          onOpenChange(!open);
        }
        if (e.key === "Escape" && open) onOpenChange(false);
      };
      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }, [open, onOpenChange]);
    if (!open) return null;
    return /* @__PURE__ */ jsxs13("div", { className: "fixed inset0 z-[var(-ZModal)] flex itemsStart justifyCenter pt-[20vh]", children: [
      /* @__PURE__ */ jsx18("div", { className: "fixed inset0 bgBlack/50", onClick: () => onOpenChange(false) }),
      /* @__PURE__ */ jsxs13(
        "div",
        {
          className: cn(
            "relative wFull maxWLg rounded-[var(-RadiusXl)] border border-[var(-BorderDefault)] bg-[var(-BgPrimary)] shadow-[var(-ShadowLg)] overflowHidden",
            className
          ),
          ref,
          ...props,
          children: [
            /* @__PURE__ */ jsx18(
              "input",
              {
                ref: inputRef,
                value: query,
                onChange: (e) => setQuery(e.target.value),
                placeholder,
                className: "wFull borderB border-[var(-BorderDefault)] bgTransparent px4 py3 text-[var(-FontSizeBase)] text-[var(-TextPrimary)] placeholder:text-[var(-TextTertiary)] outlineNone"
              }
            ),
            /* @__PURE__ */ jsxs13("div", { className: "maxH80 overflowYAuto p2", children: [
              Object.entries(grouped).map(([group, items]) => /* @__PURE__ */ jsxs13("div", { children: [
                /* @__PURE__ */ jsx18("span", { className: "px2 py1 text-[var(-FontSizeXs)] fontMedium text-[var(-TextTertiary)]", children: group }),
                items.map((cmd) => /* @__PURE__ */ jsxs13(
                  "button",
                  {
                    onClick: () => {
                      onSelect(cmd);
                      onOpenChange(false);
                    },
                    className: "flex wFull itemsCenter justifyBetween rounded-[var(-RadiusMd)] px2 py1.5 text-[var(-FontSizeSm)] text-[var(-TextPrimary)] hover:bg-[var(-BgTertiary)] transitionColors duration-[var(-DurationFast)]",
                    children: [
                      /* @__PURE__ */ jsx18("span", { children: cmd.label }),
                      cmd.shortcut && /* @__PURE__ */ jsx18("kbd", { className: "rounded border border-[var(-BorderDefault)] bg-[var(-BgSecondary)] px1.5 py0.5 fontMono text-[0.625rem] text-[var(-TextTertiary)]", children: cmd.shortcut })
                    ]
                  },
                  cmd.id
                ))
              ] }, group)),
              filtered.length === 0 && /* @__PURE__ */ jsx18("p", { className: "px2 py4 textCenter text-[var(-FontSizeSm)] text-[var(-TextTertiary)]", children: "No commands found" })
            ] })
          ]
        }
      )
    ] });
  }
);
CommandPalette.displayName = "CommandPalette";

// packages/ui/src/components/dashboard/credit-gauge.tsx
import * as React19 from "react";
import { jsx as jsx19, jsxs as jsxs14 } from "react/jsx-runtime";
var CreditGauge = React19.forwardRef(
  ({ className, used, total, tier, ...props }, ref) => {
    const percentage = Math.min(used / total * 100, 100);
    const radius = 44;
    const circumference = 2 * Math.PI * radius;
    const arcLength = circumference * 0.75;
    const offset = arcLength - percentage / 100 * arcLength;
    const color = percentage > 90 ? "var(-ColorDanger500)" : percentage > 70 ? "var(-ColorWarning500)" : "var(-Accent)";
    return /* @__PURE__ */ jsxs14("div", { className: cn("flex flexCol itemsCenter gap-[var(-Spacing2)]", className), ref, ...props, children: [
      /* @__PURE__ */ jsxs14("div", { className: "relative", children: [
        /* @__PURE__ */ jsxs14("svg", { width: "120", height: "100", viewBox: "0 0 120 100", children: [
          /* @__PURE__ */ jsx19(
            "circle",
            {
              cx: "60",
              cy: "60",
              r: radius,
              fill: "none",
              stroke: "var(-BgTertiary)",
              strokeWidth: "8",
              strokeDasharray: `${arcLength} ${circumference}`,
              strokeLinecap: "round",
              transform: "rotate(135 60 60)"
            }
          ),
          /* @__PURE__ */ jsx19(
            "circle",
            {
              cx: "60",
              cy: "60",
              r: radius,
              fill: "none",
              stroke: color,
              strokeWidth: "8",
              strokeDasharray: `${arcLength} ${circumference}`,
              strokeDashoffset: offset,
              strokeLinecap: "round",
              transform: "rotate(135 60 60)",
              className: "transitionAll duration-[var(-DurationSlow)]"
            }
          )
        ] }),
        /* @__PURE__ */ jsxs14("div", { className: "absolute inset0 flex flexCol itemsCenter justifyCenter pt2", children: [
          /* @__PURE__ */ jsx19("span", { className: "fontMono text-[var(-FontSize2xl)] fontBold text-[var(-TextPrimary)]", children: total - used }),
          /* @__PURE__ */ jsx19("span", { className: "text-[var(-FontSizeXs)] text-[var(-TextTertiary)]", children: "remaining" })
        ] })
      ] }),
      /* @__PURE__ */ jsx19("span", { className: "rounded-[var(-RadiusFull)] bg-[var(-Accent)]/15 px2.5 py0.5 text-[var(-FontSizeXs)] fontSemibold text-[var(-Accent)]", children: tier })
    ] });
  }
);
CreditGauge.displayName = "CreditGauge";

// packages/ui/src/components/dashboard/agent-avatar.tsx
import * as React20 from "react";
import { jsx as jsx20 } from "react/jsx-runtime";
var agentColors = {
  G: "bg-[var(-ColorSuccess500)]",
  /* Git */
  F: "bg-[var(-ColorInfo500)]",
  /* File */
  S: "bg-[var(-ColorWarning500)]",
  /* Shell */
  D: "bg-[var(-ColorChart5)]",
  /* Docs */
  R: "bg-[var(-ColorDanger500)]"
  /* Review */
};
var sizeStyles = {
  sm: "h5 w5 text-[0.5rem]",
  md: "h7 w7 text-[0.625rem]",
  lg: "h9 w9 text-[var(-FontSizeXs)]"
};
var AgentAvatar = React20.forwardRef(
  ({ className, agent, size = "md", ...props }, ref) => {
    const initial = agent[0]?.toUpperCase() ?? "?";
    const colorClass = agentColors[initial] ?? "bg-[var(-ColorNeutral500)]";
    return /* @__PURE__ */ jsx20(
      "span",
      {
        className: cn(
          "inlineFlex itemsCenter justifyCenter roundedFull fontBold textWhite",
          sizeStyles[size],
          colorClass,
          className
        ),
        ref,
        title: agent,
        ...props,
        children: initial
      }
    );
  }
);
AgentAvatar.displayName = "AgentAvatar";

// packages/ui/src/components/sales/pipeline-stage.tsx
import * as React21 from "react";
import { jsx as jsx21, jsxs as jsxs15 } from "react/jsx-runtime";
var PipelineStage = React21.forwardRef(({ className, stage, count, value, ...props }, ref) => /* @__PURE__ */ jsxs15("div", { ref, className: cn("flex flexCol itemsCenter gap-[var(-SpacingXs)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingMd)]", className), ...props, children: [
  /* @__PURE__ */ jsx21("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)] uppercase trackingWider", children: stage }),
  /* @__PURE__ */ jsx21("span", { className: "fontMono text-[var(-FontXl)] fontBold text-[var(-TextPrimary)]", children: count }),
  /* @__PURE__ */ jsxs15("span", { className: "fontMono text-[var(-FontXs)] text-[var(-AccentTeal400)]", children: [
    "$",
    (value / 1e3).toFixed(0),
    "K"
  ] })
] }));
PipelineStage.displayName = "PipelineStage";

// packages/ui/src/components/sales/deal-card.tsx
import * as React22 from "react";
import { jsx as jsx22, jsxs as jsxs16 } from "react/jsx-runtime";
var DealCard = React22.forwardRef(({ className, company, value, stage, probability, owner, ...props }, ref) => /* @__PURE__ */ jsxs16("div", { ref, className: cn("flex flexCol gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsxs16("div", { className: "flex itemsCenter justifyBetween", children: [
    /* @__PURE__ */ jsx22("span", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: company }),
    /* @__PURE__ */ jsxs16("span", { className: "fontMono text-[var(-FontSm)] text-[var(-AccentTeal400)]", children: [
      "$",
      (value / 1e3).toFixed(0),
      "K"
    ] })
  ] }),
  /* @__PURE__ */ jsxs16("div", { className: "flex itemsCenter justifyBetween text-[var(-FontXs)]", children: [
    /* @__PURE__ */ jsx22("span", { className: "rounded-[var(-RadiusSm)] bg-[var(-BgTertiary)] px1.5 py0.5 text-[var(-TextMuted)]", children: stage }),
    /* @__PURE__ */ jsxs16("span", { className: "text-[var(-TextSecondary)]", children: [
      probability,
      "%"
    ] }),
    /* @__PURE__ */ jsx22("span", { className: "text-[var(-TextMuted)]", children: owner })
  ] })
] }));
DealCard.displayName = "DealCard";

// packages/ui/src/components/sales/forecast-chart.tsx
import * as React23 from "react";
import { jsx as jsx23, jsxs as jsxs17 } from "react/jsx-runtime";
var ForecastChart = React23.forwardRef(({ className, data, target, ...props }, ref) => {
  const max = Math.max(...data.map((d) => Math.max(d.actual, d.forecast)), target);
  return /* @__PURE__ */ jsxs17("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
    /* @__PURE__ */ jsxs17("div", { className: "flex itemsCenter justifyBetween mb-[var(-SpacingMd)]", children: [
      /* @__PURE__ */ jsx23("span", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Revenue Forecast" }),
      /* @__PURE__ */ jsxs17("span", { className: "fontMono text-[var(-FontXs)] text-[var(-TextMuted)]", children: [
        "Target: $",
        (target / 1e3).toFixed(0),
        "K"
      ] })
    ] }),
    /* @__PURE__ */ jsx23("div", { className: "flex itemsEnd gap-[var(-SpacingXs)] h24", children: data.map((d, i) => /* @__PURE__ */ jsxs17("div", { className: "flex1 flex flexCol itemsCenter gap0.5", children: [
      /* @__PURE__ */ jsxs17("div", { className: "wFull flex gap0.5", children: [
        /* @__PURE__ */ jsx23("div", { className: "flex1 bg-[var(-AccentTeal500)]/60 roundedT-[var(-RadiusSm)]", style: { height: `${d.actual / max * 80}px` } }),
        /* @__PURE__ */ jsx23("div", { className: "flex1 bg-[var(-ModelDeepseek)]/40 roundedT-[var(-RadiusSm)]", style: { height: `${d.forecast / max * 80}px` } })
      ] }),
      /* @__PURE__ */ jsx23("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: d.month })
    ] }, i)) })
  ] });
});
ForecastChart.displayName = "ForecastChart";

// packages/ui/src/components/finance/revenue-chart.tsx
import * as React24 from "react";
import { jsx as jsx24, jsxs as jsxs18 } from "react/jsx-runtime";
var RevenueChart = React24.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs18("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx24("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Revenue" }),
  /* @__PURE__ */ jsx24("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: label || "Component ready" })
] }));
RevenueChart.displayName = "RevenueChart";

// packages/ui/src/components/finance/budget-bar.tsx
import * as React25 from "react";
import { jsx as jsx25, jsxs as jsxs19 } from "react/jsx-runtime";
var BudgetBar = React25.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs19("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx25("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Budget" }),
  /* @__PURE__ */ jsx25("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: label || "Component ready" })
] }));
BudgetBar.displayName = "BudgetBar";

// packages/ui/src/components/marketing/mekong-motif.tsx
import * as React26 from "react";
import { jsx as jsx26, jsxs as jsxs20 } from "react/jsx-runtime";
var MekongMotif = React26.forwardRef(
  ({ className, variant = "horizontal", ...props }, ref) => {
    if (variant === "radial") {
      return /* @__PURE__ */ jsx26(
        "svg",
        {
          className: cn("text-[var(--accent)]", className),
          viewBox: "0 0 200 200",
          fill: "none",
          ref,
          ...props,
          children: /* @__PURE__ */ jsx26("g", { stroke: "currentColor", strokeWidth: "0.5", opacity: "0.15", children: [0, 45, 90, 135, 180, 225, 270, 315].map((angle) => /* @__PURE__ */ jsx26(
            "path",
            {
              d: `M100,100 Q${100 + 30 * Math.cos(angle * Math.PI / 180)},${100 + 30 * Math.sin(angle * Math.PI / 180)} ${100 + 80 * Math.cos((angle + 10) * Math.PI / 180)},${100 + 80 * Math.sin((angle + 10) * Math.PI / 180)}`
            },
            angle
          )) })
        }
      );
    }
    return /* @__PURE__ */ jsx26(
      "svg",
      {
        className: cn("text-[var(--accent)]", className),
        viewBox: "0 0 400 100",
        fill: "none",
        ref,
        ...props,
        children: /* @__PURE__ */ jsxs20("g", { stroke: "currentColor", strokeWidth: "0.5", opacity: "0.15", children: [
          /* @__PURE__ */ jsx26("path", { d: "M200,10 Q160,30 100,50 Q60,65 20,90" }),
          /* @__PURE__ */ jsx26("path", { d: "M200,10 Q190,35 180,50 Q170,65 160,90" }),
          /* @__PURE__ */ jsx26("path", { d: "M200,10 Q210,30 230,50 Q260,70 300,90" }),
          /* @__PURE__ */ jsx26("path", { d: "M200,10 Q220,25 260,40 Q320,60 380,80" }),
          /* @__PURE__ */ jsx26("path", { d: "M200,10 Q195,40 200,55 Q205,70 200,90" })
        ] })
      }
    );
  }
);
MekongMotif.displayName = "MekongMotif";

// packages/ui/src/components/marketing/feature-bento.tsx
import * as React27 from "react";
import { jsx as jsx27, jsxs as jsxs21 } from "react/jsx-runtime";
var FeatureBento = React27.forwardRef(
  ({ className, items, ...props }, ref) => /* @__PURE__ */ jsx27(
    "div",
    {
      className: cn(
        "grid autoRows-[minmax(180px,auto)] gridCols1 gap-[var(-Spacing4)] md:gridCols3",
        className
      ),
      ref,
      ...props,
      children: items.map((item, i) => /* @__PURE__ */ jsxs21(
        "div",
        {
          className: cn(
            "group flex flexCol gap-[var(-Spacing4)] overflowHidden rounded-[var(-RadiusXl)] border border-[var(-BorderDefault)] bg-[var(-BgPrimary)] p-[var(-Spacing6)] transitionShadow duration-[var(-DurationNormal)] hover:shadow-[var(-ShadowMd)]",
            item.span === "2" && "md:colSpan2"
          ),
          children: [
            item.icon && /* @__PURE__ */ jsx27("span", { className: "text-[var(-Accent)]", children: item.icon }),
            /* @__PURE__ */ jsx27("h3", { className: "text-[var(-FontSizeLg)] fontSemibold text-[var(-TextPrimary)]", children: item.title }),
            /* @__PURE__ */ jsx27("p", { className: "text-[var(-FontSizeSm)] text-[var(-TextSecondary)] leadingRelaxed", children: item.description }),
            item.demo && /* @__PURE__ */ jsx27("div", { className: "mtAuto", children: item.demo })
          ]
        },
        i
      ))
    }
  )
);
FeatureBento.displayName = "FeatureBento";

// packages/ui/src/components/marketing/hero-section.tsx
import * as React28 from "react";
import { jsx as jsx28, jsxs as jsxs22 } from "react/jsx-runtime";
var HeroSection = React28.forwardRef(
  ({ className, title, subtitle, primaryCta, secondaryCta, terminal, ...props }, ref) => /* @__PURE__ */ jsxs22(
    "section",
    {
      className: cn(
        "flex minH-[80vh] flexCol itemsCenter justifyCenter gap-[var(-Spacing8)] px-[var(-Spacing6)] py-[var(-Spacing24)] textCenter",
        className
      ),
      ref,
      ...props,
      children: [
        /* @__PURE__ */ jsxs22("div", { className: "flex maxW3xl flexCol itemsCenter gap-[var(-Spacing6)]", children: [
          /* @__PURE__ */ jsx28("h1", { className: "text-[var(-FontSizeHero)] fontBold leading-[1.1] trackingTight text-[var(-TextPrimary)]", children: title }),
          /* @__PURE__ */ jsx28("p", { className: "maxWXl text-[var(-FontSizeLg)] text-[var(-TextSecondary)] leadingRelaxed", children: subtitle }),
          /* @__PURE__ */ jsxs22("div", { className: "flex itemsCenter gap-[var(-Spacing4)]", children: [
            primaryCta && /* @__PURE__ */ jsx28(
              "a",
              {
                href: primaryCta.href,
                className: "inlineFlex h12 itemsCenter rounded-[var(-RadiusLg)] bg-[var(-Accent)] px8 text-[var(-FontSizeBase)] fontSemibold text-[var(-AccentText)] transitionColors duration-[var(-DurationNormal)] hover:bg-[var(-AccentHover)]",
                children: primaryCta.label
              }
            ),
            secondaryCta && /* @__PURE__ */ jsx28(
              "a",
              {
                href: secondaryCta.href,
                className: "inlineFlex h12 itemsCenter rounded-[var(-RadiusLg)] border border-[var(-BorderStrong)] px8 text-[var(-FontSizeBase)] fontSemibold text-[var(-TextPrimary)] transitionColors duration-[var(-DurationNormal)] hover:bg-[var(-BgTertiary)]",
                children: secondaryCta.label
              }
            )
          ] })
        ] }),
        terminal && /* @__PURE__ */ jsx28("div", { className: "wFull maxW2xl", children: terminal })
      ]
    }
  )
);
HeroSection.displayName = "HeroSection";

// packages/ui/src/components/marketing/pricing-table.tsx
import * as React29 from "react";
import { jsx as jsx29, jsxs as jsxs23 } from "react/jsx-runtime";
var PricingTable = React29.forwardRef(
  ({ className, tiers, onSelect, ...props }, ref) => /* @__PURE__ */ jsx29(
    "div",
    {
      className: cn(
        "grid gridCols1 gap-[var(-Spacing6)] md:gridCols2 lg:gridCols4",
        className
      ),
      ref,
      ...props,
      children: tiers.map((tier) => /* @__PURE__ */ jsxs23(
        "div",
        {
          className: cn(
            "flex flexCol rounded-[var(-RadiusXl)] border p-[var(-Spacing6)]",
            tier.highlighted ? "border-[var(-Accent)] bg-[var(-Accent)]/5 ring1 ring-[var(-Accent)]" : "border-[var(-BorderDefault)] bg-[var(-BgPrimary)]"
          ),
          children: [
            /* @__PURE__ */ jsx29("h3", { className: "text-[var(-FontSizeLg)] fontSemibold text-[var(-TextPrimary)]", children: tier.name }),
            /* @__PURE__ */ jsxs23("div", { className: "mt-[var(-Spacing4)]", children: [
              /* @__PURE__ */ jsx29("span", { className: "fontMono text-[var(-FontSize4xl)] fontBold text-[var(-TextPrimary)]", children: typeof tier.price === "number" ? `$${tier.price}` : tier.price }),
              typeof tier.price === "number" && /* @__PURE__ */ jsx29("span", { className: "text-[var(-FontSizeSm)] text-[var(-TextTertiary)]", children: "/mo" })
            ] }),
            /* @__PURE__ */ jsx29("p", { className: "mt1 text-[var(-FontSizeSm)] text-[var(-TextSecondary)]", children: typeof tier.credits === "number" ? `${tier.credits.toLocaleString()} credits` : tier.credits }),
            /* @__PURE__ */ jsx29("ul", { className: "mt-[var(-Spacing6)] flex flex1 flexCol gap-[var(-Spacing2)]", children: tier.features.map((feature) => /* @__PURE__ */ jsxs23("li", { className: "flex itemsStart gap2 text-[var(-FontSizeSm)] text-[var(-TextSecondary)]", children: [
              /* @__PURE__ */ jsx29("span", { className: "mt0.5 text-[var(-ColorSuccess500)]", children: "\u2713" }),
              feature
            ] }, feature)) }),
            /* @__PURE__ */ jsx29(
              "button",
              {
                onClick: () => onSelect?.(tier),
                className: cn(
                  "mt-[var(-Spacing6)] inlineFlex h10 itemsCenter justifyCenter rounded-[var(-RadiusMd)] px4 text-[var(-FontSizeSm)] fontSemibold transitionColors duration-[var(-DurationNormal)]",
                  tier.highlighted ? "bg-[var(-Accent)] text-[var(-AccentText)] hover:bg-[var(-AccentHover)]" : "border border-[var(-BorderStrong)] text-[var(-TextPrimary)] hover:bg-[var(-BgTertiary)]"
                ),
                children: tier.cta
              }
            )
          ]
        },
        tier.name
      ))
    }
  )
);
PricingTable.displayName = "PricingTable";

// packages/ui/src/components/marketing/trust-bar.tsx
import * as React30 from "react";
import { jsx as jsx30, jsxs as jsxs24 } from "react/jsx-runtime";
var TrustBar = React30.forwardRef(
  ({ className, githubStars, npmDownloads, license = "MIT", ...props }, ref) => /* @__PURE__ */ jsxs24(
    "div",
    {
      className: cn(
        "flex flexWrap itemsCenter justifyCenter gap-[var(-Spacing6)] py-[var(-Spacing4)]",
        className
      ),
      ref,
      ...props,
      children: [
        githubStars !== void 0 && /* @__PURE__ */ jsxs24("span", { className: "flex itemsCenter gap1.5 rounded-[var(-RadiusFull)] border border-[var(-BorderDefault)] bg-[var(-BgSecondary)] px3 py1 text-[var(-FontSizeSm)] text-[var(-TextSecondary)]", children: [
          /* @__PURE__ */ jsx30("svg", { width: "16", height: "16", viewBox: "0 0 16 16", fill: "currentColor", children: /* @__PURE__ */ jsx30("path", { d: "M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l3.046 2.97.719 4.192a.75.75 0 0 11.088.791L8 12.347l3.766 1.98a.75.75 0 0 11.088-.79l.724.194L.818 6.374a.75.75 0 0 1 .4161.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z" }) }),
          githubStars.toLocaleString(),
          " stars"
        ] }),
        npmDownloads !== void 0 && /* @__PURE__ */ jsxs24("span", { className: "flex itemsCenter gap1.5 rounded-[var(-RadiusFull)] border border-[var(-BorderDefault)] bg-[var(-BgSecondary)] px3 py1 text-[var(-FontSizeSm)] text-[var(-TextSecondary)]", children: [
          npmDownloads.toLocaleString(),
          " downloads"
        ] }),
        /* @__PURE__ */ jsxs24("span", { className: "flex itemsCenter gap1.5 rounded-[var(-RadiusFull)] border border-[var(-BorderDefault)] bg-[var(-BgSecondary)] px3 py1 text-[var(-FontSizeSm)] text-[var(-TextSecondary)]", children: [
          license,
          " Licensed"
        ] })
      ]
    }
  )
);
TrustBar.displayName = "TrustBar";

// packages/ui/src/components/marketing/terminal-demo.tsx
import * as React31 from "react";
import { jsx as jsx31, jsxs as jsxs25 } from "react/jsx-runtime";
var TerminalDemo = React31.forwardRef(
  ({ className, command = 'mekong cook "Build landing page"', lines = [], typingSpeed = 50, ...props }, ref) => {
    const [displayed, setDisplayed] = React31.useState("");
    const [lineIndex, setLineIndex] = React31.useState(1);
    const [showCursor, setShowCursor] = React31.useState(true);
    React31.useEffect(() => {
      let i = 0;
      const timer = setInterval(() => {
        if (i <= command.length) {
          setDisplayed(command.slice(0, i));
          i++;
        } else {
          clearInterval(timer);
          setTimeout(() => {
            setLineIndex(0);
            let li = 0;
            const lineTimer = setInterval(() => {
              if (li < lines.length) {
                setLineIndex(li);
                li++;
              } else {
                clearInterval(lineTimer);
                setShowCursor(false);
              }
            }, 400);
          }, 500);
        }
      }, typingSpeed);
      return () => clearInterval(timer);
    }, [command, lines, typingSpeed]);
    return /* @__PURE__ */ jsxs25(
      "div",
      {
        className: cn(
          "wFull maxW2xl overflowHidden rounded-[var(-RadiusXl)] border border-[var(-ColorNeutral800)] bg-[var(-ColorNeutral950)] shadow-[var(-ShadowLg)]",
          className
        ),
        ref,
        ...props,
        children: [
          /* @__PURE__ */ jsxs25("div", { className: "flex itemsCenter gap2 borderB border-[var(-ColorNeutral800)] px4 py2.5", children: [
            /* @__PURE__ */ jsx31("span", { className: "h3 w3 roundedFull bg-[var(-ColorDanger500)]" }),
            /* @__PURE__ */ jsx31("span", { className: "h3 w3 roundedFull bg-[var(-ColorWarning500)]" }),
            /* @__PURE__ */ jsx31("span", { className: "h3 w3 roundedFull bg-[var(-ColorSuccess500)]" }),
            /* @__PURE__ */ jsx31("span", { className: "ml2 text-[var(-FontSizeXs)] text-[var(-ColorNeutral500)]", children: "terminal" })
          ] }),
          /* @__PURE__ */ jsxs25("div", { className: "p4 fontMono text-[var(-FontSizeSm)] leadingRelaxed", children: [
            /* @__PURE__ */ jsxs25("div", { children: [
              /* @__PURE__ */ jsx31("span", { className: "text-[var(-ColorSuccess500)]", children: "$ " }),
              /* @__PURE__ */ jsx31("span", { className: "text-[var(-ColorNeutral100)]", children: displayed }),
              showCursor && /* @__PURE__ */ jsx31("span", { className: "animatePulse text-[var(-Accent)]", children: "|" })
            ] }),
            lineIndex >= 0 && lines.slice(0, lineIndex + 1).map((line, i) => /* @__PURE__ */ jsx31("div", { className: "text-[var(-ColorNeutral400)]", children: line }, i))
          ] })
        ]
      }
    );
  }
);
TerminalDemo.displayName = "TerminalDemo";

// packages/ui/src/components/security/policy-status.tsx
import * as React32 from "react";
import { jsx as jsx32, jsxs as jsxs26 } from "react/jsx-runtime";
var policyStatusVariants = cva(
  "inlineFlex itemsCenter rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontMedium",
  {
    variants: {
      status: {
        active: "bg-[var(-StatusHealthy)]/15 text-[var(-StatusHealthy)]",
        draft: "bg-[var(-StatusWarning)]/15 text-[var(-StatusWarning)]",
        expired: "bg-[var(-StatusError)]/15 text-[var(-StatusError)]"
      }
    },
    defaultVariants: { status: "active" }
  }
);
var PolicyStatus = React32.forwardRef(
  ({ className, policies, ...props }, ref) => /* @__PURE__ */ jsxs26(
    "div",
    {
      ref,
      className: cn(
        "flex flexCol rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] overflowHidden",
        className
      ),
      ...props,
      children: [
        /* @__PURE__ */ jsx32("div", { className: "borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)]", children: /* @__PURE__ */ jsx32("span", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Policy Compliance" }) }),
        /* @__PURE__ */ jsx32("div", { className: "flex flexCol", children: policies.map((policy, i) => /* @__PURE__ */ jsxs26(
          "div",
          {
            className: "flex itemsCenter justifyBetween borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingMd)] last:borderB0 hover:bg-[var(-SurfaceHover)]",
            children: [
              /* @__PURE__ */ jsx32("span", { className: "text-[var(-FontSm)] text-[var(-TextPrimary)]", children: policy.name }),
              /* @__PURE__ */ jsxs26("div", { className: "flex itemsCenter gap-[var(-SpacingMd)]", children: [
                /* @__PURE__ */ jsx32("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: policy.lastReview }),
                /* @__PURE__ */ jsx32("span", { className: policyStatusVariants({ status: policy.status }), children: policy.status })
              ] })
            ]
          },
          i
        )) })
      ]
    }
  )
);
PolicyStatus.displayName = "PolicyStatus";

// packages/ui/src/components/security/threat-feed.tsx
import * as React33 from "react";
import { jsx as jsx33, jsxs as jsxs27 } from "react/jsx-runtime";
var severityDot = cva("inlineBlock h2 w2 roundedFull", {
  variants: {
    severity: {
      critical: "bg-[var(-StatusError)]",
      high: "bg-[var(-StatusWarning)]",
      medium: "bg-[var(-AccentTeal400)]",
      low: "bg-[var(-StatusIdle)]",
      info: "bg-[var(-ModelQwen)]"
    }
  },
  defaultVariants: { severity: "info" }
});
var ThreatFeed = React33.forwardRef(
  ({ className, events, ...props }, ref) => /* @__PURE__ */ jsxs27(
    "div",
    {
      ref,
      className: cn(
        "flex flexCol rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] overflowHidden",
        className
      ),
      ...props,
      children: [
        /* @__PURE__ */ jsx33("div", { className: "borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)]", children: /* @__PURE__ */ jsx33("span", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Threat Feed" }) }),
        /* @__PURE__ */ jsx33("div", { className: "flex maxH80 flexCol overflowYAuto", children: events.map((event, i) => /* @__PURE__ */ jsxs27(
          "div",
          {
            className: "flex itemsCenter gap-[var(-SpacingMd)] borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)] last:borderB0 hover:bg-[var(-SurfaceHover)]",
            children: [
              /* @__PURE__ */ jsx33("span", { className: severityDot({ severity: event.severity }) }),
              /* @__PURE__ */ jsx33("span", { className: "minW-[60px] fontMono text-[var(-FontXs)] text-[var(-TextMuted)]", children: event.time }),
              /* @__PURE__ */ jsx33("span", { className: "flex1 text-[var(-FontSm)] text-[var(-TextPrimary)]", children: event.type }),
              /* @__PURE__ */ jsx33("span", { className: "text-[var(-FontXs)] text-[var(-TextSecondary)]", children: event.source })
            ]
          },
          i
        )) })
      ]
    }
  )
);
ThreatFeed.displayName = "ThreatFeed";

// packages/ui/src/components/security/compliance-gauge.tsx
import * as React34 from "react";
import { jsx as jsx34, jsxs as jsxs28 } from "react/jsx-runtime";
var ComplianceGauge = React34.forwardRef(
  ({ className, framework, score, maxScore, ...props }, ref) => {
    const pct = Math.round(score / maxScore * 100);
    const radius = 40;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - pct / 100 * circumference;
    const color = pct >= 90 ? "var(-StatusHealthy)" : pct >= 70 ? "var(-StatusWarning)" : "var(-StatusError)";
    return /* @__PURE__ */ jsxs28(
      "div",
      {
        ref,
        className: cn(
          "flex flexCol itemsCenter gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]",
          className
        ),
        ...props,
        children: [
          /* @__PURE__ */ jsxs28("svg", { width: "100", height: "100", viewBox: "0 0 100 100", children: [
            /* @__PURE__ */ jsx34(
              "circle",
              {
                cx: "50",
                cy: "50",
                r: radius,
                fill: "none",
                stroke: "var(-BorderDefault)",
                strokeWidth: "8"
              }
            ),
            /* @__PURE__ */ jsx34(
              "circle",
              {
                cx: "50",
                cy: "50",
                r: radius,
                fill: "none",
                stroke: color,
                strokeWidth: "8",
                strokeDasharray: circumference,
                strokeDashoffset: offset,
                strokeLinecap: "round",
                transform: "rotate(90 50 50)",
                style: { transition: "strokeDashoffset 0.6s ease" }
              }
            ),
            /* @__PURE__ */ jsxs28(
              "text",
              {
                x: "50",
                y: "46",
                textAnchor: "middle",
                fill: "var(-TextPrimary)",
                fontSize: "var(-FontXl)",
                fontWeight: "bold",
                fontFamily: "var(-FontFamilyMono)",
                children: [
                  pct,
                  "%"
                ]
              }
            ),
            /* @__PURE__ */ jsxs28(
              "text",
              {
                x: "50",
                y: "62",
                textAnchor: "middle",
                fill: "var(-TextMuted)",
                fontSize: "var(-FontXs)",
                fontFamily: "var(-FontFamilySans)",
                children: [
                  score,
                  "/",
                  maxScore
                ]
              }
            )
          ] }),
          /* @__PURE__ */ jsx34("span", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: framework })
        ]
      }
    );
  }
);
ComplianceGauge.displayName = "ComplianceGauge";

// packages/ui/src/components/security/incident-timeline.tsx
import * as React35 from "react";
import { jsx as jsx35, jsxs as jsxs29 } from "react/jsx-runtime";
var stepIndicator = cva(
  "flex h8 w8 itemsCenter justifyCenter roundedFull text-[var(-FontXs)] fontBold",
  {
    variants: {
      status: {
        done: "bg-[var(-StatusHealthy)] text-[var(-BgPrimary)]",
        active: "bg-[var(-AccentTeal500)] text-[var(-BgPrimary)] animatePulse",
        pending: "bg-[var(-BgTertiary)] text-[var(-TextMuted)]"
      }
    },
    defaultVariants: { status: "pending" }
  }
);
var stepLine = cva("h0.5 flex1", {
  variants: {
    status: {
      done: "bg-[var(-StatusHealthy)]",
      active: "bg-[var(-AccentTeal500)]",
      pending: "bg-[var(-BorderDefault)]"
    }
  },
  defaultVariants: { status: "pending" }
});
var IncidentTimeline = React35.forwardRef(
  ({ className, steps, ...props }, ref) => /* @__PURE__ */ jsxs29(
    "div",
    {
      ref,
      className: cn(
        "rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]",
        className
      ),
      ...props,
      children: [
        /* @__PURE__ */ jsx35("div", { className: "mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Incident Response Pipeline" }),
        /* @__PURE__ */ jsx35("div", { className: "flex itemsCenter", children: steps.map((step, i) => /* @__PURE__ */ jsxs29(React35.Fragment, { children: [
          /* @__PURE__ */ jsxs29("div", { className: "flex flexCol itemsCenter gap-[var(-SpacingXs)]", children: [
            /* @__PURE__ */ jsx35("span", { className: stepIndicator({ status: step.status }), children: step.status === "done" ? "\u2713" : i + 1 }),
            /* @__PURE__ */ jsx35("span", { className: "text-[var(-FontXs)] text-[var(-TextSecondary)] whitespaceNowrap", children: step.name }),
            step.duration && /* @__PURE__ */ jsx35("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: step.duration })
          ] }),
          i < steps.length - 1 && /* @__PURE__ */ jsx35("div", { className: cn(stepLine({ status: step.status }), "mx1 minW-[24px]") })
        ] }, i)) })
      ]
    }
  )
);
IncidentTimeline.displayName = "IncidentTimeline";

// packages/ui/src/components/security/vuln-card.tsx
import * as React36 from "react";
import { jsx as jsx36, jsxs as jsxs30 } from "react/jsx-runtime";
var vulnSeverityVariants = cva(
  "inlineFlex itemsCenter rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontBold uppercase trackingWider",
  {
    variants: {
      severity: {
        critical: "bg-[var(-StatusError)]/20 text-[var(-StatusError)]",
        high: "bg-[var(-StatusWarning)]/20 text-[var(-StatusWarning)]",
        medium: "bg-[var(-AccentTeal500)]/20 text-[var(-AccentTeal400)]",
        low: "bg-[var(-StatusIdle)]/20 text-[var(-StatusIdle)]"
      }
    },
    defaultVariants: { severity: "medium" }
  }
);
var VulnCard = React36.forwardRef(
  ({ className, cve, severity, component, slaHours, status, ...props }, ref) => /* @__PURE__ */ jsxs30(
    "div",
    {
      ref,
      className: cn(
        "flex flexCol gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]",
        className
      ),
      ...props,
      children: [
        /* @__PURE__ */ jsxs30("div", { className: "flex itemsCenter justifyBetween", children: [
          /* @__PURE__ */ jsx36("span", { className: "fontMono text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: cve }),
          /* @__PURE__ */ jsx36("span", { className: vulnSeverityVariants({ severity }), children: severity })
        ] }),
        /* @__PURE__ */ jsx36("span", { className: "text-[var(-FontSm)] text-[var(-TextSecondary)]", children: component }),
        /* @__PURE__ */ jsxs30("div", { className: "flex itemsCenter justifyBetween borderT border-[var(-BorderDefault)] pt-[var(-SpacingSm)]", children: [
          /* @__PURE__ */ jsxs30("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: [
            "SLA: ",
            slaHours,
            "h"
          ] }),
          /* @__PURE__ */ jsx36("span", { className: "text-[var(-FontXs)] fontMedium text-[var(-TextSecondary)]", children: status })
        ] })
      ]
    }
  )
);
VulnCard.displayName = "VulnCard";

// packages/ui/src/components/security/access-matrix.tsx
import * as React37 from "react";
import { jsx as jsx37, jsxs as jsxs31 } from "react/jsx-runtime";
var cellColor = {
  allow: "bg-[var(-PermAllow)]/20 text-[var(-PermAllow)]",
  deny: "bg-[var(-PermDeny)]/20 text-[var(-PermDeny)]",
  na: "bg-[var(-BgTertiary)] text-[var(-TextMuted)]"
};
var cellLabel = {
  allow: "\u2713",
  deny: "\u2717",
  na: "\u2014"
};
var AccessMatrix = React37.forwardRef(
  ({ className, roles, systems, permissions, ...props }, ref) => /* @__PURE__ */ jsx37(
    "div",
    {
      ref,
      className: cn(
        "overflowXAuto rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)]",
        className
      ),
      ...props,
      children: /* @__PURE__ */ jsxs31("table", { className: "wFull borderCollapse text-[var(-FontXs)]", children: [
        /* @__PURE__ */ jsx37("thead", { children: /* @__PURE__ */ jsxs31("tr", { className: "borderB border-[var(-BorderDefault)]", children: [
          /* @__PURE__ */ jsx37("th", { className: "sticky left0 bg-[var(-SurfaceCard)] px-[var(-SpacingMd)] py-[var(-SpacingSm)] textLeft fontSemibold text-[var(-TextSecondary)]", children: "Role / System" }),
          systems.map((sys) => /* @__PURE__ */ jsx37(
            "th",
            {
              className: "px-[var(-SpacingMd)] py-[var(-SpacingSm)] textCenter fontSemibold text-[var(-TextSecondary)]",
              children: sys
            },
            sys
          ))
        ] }) }),
        /* @__PURE__ */ jsx37("tbody", { children: roles.map((role) => /* @__PURE__ */ jsxs31(
          "tr",
          {
            className: "borderB border-[var(-BorderDefault)] last:borderB0 hover:bg-[var(-SurfaceHover)]",
            children: [
              /* @__PURE__ */ jsx37("td", { className: "sticky left0 bg-[var(-SurfaceCard)] px-[var(-SpacingMd)] py-[var(-SpacingSm)] fontMedium text-[var(-TextPrimary)]", children: role }),
              systems.map((sys) => {
                const perm = permissions[role]?.[sys] ?? "na";
                return /* @__PURE__ */ jsx37("td", { className: "px-[var(-SpacingMd)] py-[var(-SpacingSm)] textCenter", children: /* @__PURE__ */ jsx37(
                  "span",
                  {
                    className: cn(
                      "inlineFlex h6 w6 itemsCenter justifyCenter rounded-[var(-RadiusSm)] text-[var(-FontXs)] fontBold",
                      cellColor[perm]
                    ),
                    children: cellLabel[perm]
                  }
                ) }, sys);
              })
            ]
          },
          role
        )) })
      ] })
    }
  )
);
AccessMatrix.displayName = "AccessMatrix";

// packages/ui/src/components/trading/order-book.tsx
import * as React38 from "react";
import { jsx as jsx38, jsxs as jsxs32 } from "react/jsx-runtime";
var OrderBook = React38.forwardRef(
  ({ className, bids, asks, maxDepth, ...props }, ref) => {
    const max = maxDepth ?? Math.max(
      ...bids.map((b) => b.size),
      ...asks.map((a) => a.size),
      1
    );
    const renderRow = (row, side) => /* @__PURE__ */ jsxs32("div", { className: "relative flex itemsCenter justifyBetween px3 py1", children: [
      /* @__PURE__ */ jsx38(
        "div",
        {
          className: cn(
            "absolute insetY0 opacity15",
            side === "bid" ? "left0 bg-[var(-ColorBid)]" : "right0 bg-[var(-ColorAsk)]"
          ),
          style: { width: `${row.size / max * 100}%` }
        }
      ),
      /* @__PURE__ */ jsx38("span", { className: cn(
        "relative z10 fontMono text-[var(-FontSizeSm)]",
        side === "bid" ? "text-[var(-ColorBid)]" : "text-[var(-ColorAsk)]"
      ), children: row.price.toFixed(2) }),
      /* @__PURE__ */ jsx38("span", { className: cn(
        "relative z10 fontMono text-[var(-FontSizeSm)] text-[var(-TextSecondary)]",
        row.isBot && "underline decorationDotted"
      ), children: row.size.toLocaleString() })
    ] }, `${side}-${row.price}`);
    return /* @__PURE__ */ jsxs32(
      "div",
      {
        className: cn(
          "rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-BgPrimary)] overflowHidden",
          className
        ),
        ref,
        ...props,
        children: [
          /* @__PURE__ */ jsxs32("div", { className: "flex itemsCenter justifyBetween borderB border-[var(-BorderDefault)] px3 py2", children: [
            /* @__PURE__ */ jsx38("span", { className: "text-[var(-FontSizeXs)] fontMedium text-[var(-TextSecondary)]", children: "Price" }),
            /* @__PURE__ */ jsx38("span", { className: "text-[var(-FontSizeXs)] fontMedium text-[var(-TextSecondary)]", children: "Size" })
          ] }),
          /* @__PURE__ */ jsxs32("div", { className: "flex flexCol", children: [
            asks.slice().reverse().map((row) => renderRow(row, "ask")),
            /* @__PURE__ */ jsx38("div", { className: "borderY border-[var(-BorderDefault)] bg-[var(-BgSecondary)] px3 py1 textCenter", children: /* @__PURE__ */ jsx38("span", { className: "text-[var(-FontSizeXs)] fontMedium text-[var(-TextTertiary)]", children: "Spread" }) }),
            bids.map((row) => renderRow(row, "bid"))
          ] })
        ]
      }
    );
  }
);
OrderBook.displayName = "OrderBook";

// packages/ui/src/components/trading/position-card.tsx
import * as React39 from "react";
import { jsx as jsx39, jsxs as jsxs33 } from "react/jsx-runtime";
var PositionCard = React39.forwardRef(
  ({ className, question, probability, positionSize, unrealizedPnl, sparkline, ...props }, ref) => /* @__PURE__ */ jsxs33(
    "div",
    {
      className: cn(
        "flex flexCol gap-[var(-Spacing3)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-BgSecondary)] p-[var(-Spacing4)]",
        className
      ),
      ref,
      ...props,
      children: [
        /* @__PURE__ */ jsx39("p", { className: "text-[var(-FontSizeSm)] fontMedium text-[var(-TextPrimary)] leadingSnug", children: question }),
        /* @__PURE__ */ jsxs33("div", { className: "flex itemsCenter justifyBetween", children: [
          /* @__PURE__ */ jsxs33("div", { className: "flex flexCol", children: [
            /* @__PURE__ */ jsx39("span", { className: "text-[var(-FontSizeXs)] text-[var(-TextTertiary)]", children: "Probability" }),
            /* @__PURE__ */ jsxs33("span", { className: "fontMono text-[var(-FontSizeXl)] fontBold text-[var(-TextPrimary)]", children: [
              probability,
              "%"
            ] })
          ] }),
          /* @__PURE__ */ jsxs33("div", { className: "flex flexCol itemsEnd", children: [
            /* @__PURE__ */ jsx39("span", { className: "text-[var(-FontSizeXs)] text-[var(-TextTertiary)]", children: "Position" }),
            /* @__PURE__ */ jsxs33("span", { className: "fontMono text-[var(-FontSizeSm)] text-[var(-TextSecondary)]", children: [
              "$",
              positionSize.toLocaleString()
            ] })
          ] })
        ] }),
        /* @__PURE__ */ jsxs33("div", { className: "flex itemsCenter justifyBetween borderT border-[var(-BorderDefault)] pt-[var(-Spacing2)]", children: [
          /* @__PURE__ */ jsxs33(
            "span",
            {
              className: cn(
                "fontMono text-[var(-FontSizeSm)] fontSemibold",
                unrealizedPnl >= 0 ? "text-[var(-ColorGain)]" : "text-[var(-ColorLoss)]"
              ),
              children: [
                unrealizedPnl >= 0 ? "+" : "",
                unrealizedPnl.toFixed(2)
              ]
            }
          ),
          sparkline && /* @__PURE__ */ jsx39("div", { className: "h6 w16", children: sparkline })
        ] })
      ]
    }
  )
);
PositionCard.displayName = "PositionCard";

// packages/ui/src/components/trading/price-display.tsx
import * as React40 from "react";
import { jsxs as jsxs34 } from "react/jsx-runtime";
var PriceDisplay = React40.forwardRef(
  ({ className, value, previousValue, currency = "$", decimals = 2, ...props }, ref) => {
    const direction = previousValue !== void 0 ? value > previousValue ? "up" : value < previousValue ? "down" : "flat" : "flat";
    const [flash, setFlash] = React40.useState(false);
    React40.useEffect(() => {
      if (previousValue !== void 0 && value !== previousValue) {
        setFlash(true);
        const timer = setTimeout(() => setFlash(false), 300);
        return () => clearTimeout(timer);
      }
    }, [value, previousValue]);
    return /* @__PURE__ */ jsxs34(
      "span",
      {
        className: cn(
          "fontMono text-[var(-FontSizeLg)] fontBold tabularNums transitionColors duration-[var(-DurationFast)]",
          direction === "up" && "text-[var(-ColorGain)]",
          direction === "down" && "text-[var(-ColorLoss)]",
          direction === "flat" && "text-[var(-TextPrimary)]",
          flash && "scale105",
          className
        ),
        ref,
        ...props,
        children: [
          currency,
          value.toFixed(decimals)
        ]
      }
    );
  }
);
PriceDisplay.displayName = "PriceDisplay";

// packages/ui/src/components/trading/activity-feed.tsx
import * as React41 from "react";
import { jsx as jsx40, jsxs as jsxs35 } from "react/jsx-runtime";
var actionColors = {
  buy: "bg-[var(-ColorGain)]/15 text-[var(-ColorGain)]",
  sell: "bg-[var(-ColorLoss)]/15 text-[var(-ColorLoss)]",
  hedge: "bg-[var(-ColorInfo500)]/15 text-[var(-ColorInfo500)]",
  rebalance: "bg-[var(-ColorWarning500)]/15 text-[var(-ColorWarning500)]"
};
var ActivityFeed = React41.forwardRef(
  ({ className, items, maxItems = 20, ...props }, ref) => /* @__PURE__ */ jsxs35(
    "div",
    {
      className: cn(
        "flex flexCol overflowYAuto rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-BgPrimary)]",
        className
      ),
      ref,
      ...props,
      children: [
        /* @__PURE__ */ jsx40("div", { className: "sticky top0 borderB border-[var(-BorderDefault)] bg-[var(-BgPrimary)] px4 py2", children: /* @__PURE__ */ jsx40("span", { className: "text-[var(-FontSizeSm)] fontMedium text-[var(-TextSecondary)]", children: "Activity" }) }),
        items.slice(0, maxItems).map((item) => /* @__PURE__ */ jsxs35("div", { className: "flex itemsCenter gap3 borderB border-[var(-BorderDefault)] px4 py2.5 last:border0", children: [
          /* @__PURE__ */ jsx40("span", { className: "text-[var(-FontSizeXs)] text-[var(-TextTertiary)] tabularNums whitespaceNowrap", children: item.timestamp }),
          /* @__PURE__ */ jsx40("span", { className: cn(
            "rounded-[var(-RadiusFull)] px2 py0.5 text-[0.625rem] fontSemibold uppercase",
            actionColors[item.actionType]
          ), children: item.actionType }),
          /* @__PURE__ */ jsx40("span", { className: "flex1 truncate text-[var(-FontSizeSm)] text-[var(-TextPrimary)]", children: item.description }),
          item.amount !== void 0 && /* @__PURE__ */ jsxs35("span", { className: "fontMono text-[var(-FontSizeSm)] text-[var(-TextSecondary)]", children: [
            "$",
            item.amount.toLocaleString()
          ] })
        ] }, item.id))
      ]
    }
  )
);
ActivityFeed.displayName = "ActivityFeed";

// packages/ui/src/components/trading/probability-chart.tsx
import * as React42 from "react";
import { jsx as jsx41, jsxs as jsxs36 } from "react/jsx-runtime";
var ProbabilityChart = React42.forwardRef(
  ({ className, data, height = 200, color, ...props }, ref) => {
    const chartColor = color ?? "var(-Accent)";
    const min = Math.min(...data.map((d) => d.value));
    const max = Math.max(...data.map((d) => d.value));
    const range = max - min || 1;
    const points = data.map((d, i) => {
      const x = i / (data.length - 1) * 100;
      const y = 100 - (d.value - min) / range * 100;
      return `${x},${y}`;
    }).join(" ");
    const areaPoints = `0,100 ${points} 100,100`;
    return /* @__PURE__ */ jsx41(
      "div",
      {
        className: cn(
          "rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-BgPrimary)] p-[var(-Spacing4)]",
          className
        ),
        ref,
        style: { height },
        ...props,
        children: /* @__PURE__ */ jsxs36(
          "svg",
          {
            viewBox: "0 0 100 100",
            preserveAspectRatio: "none",
            className: "hFull wFull",
            children: [
              /* @__PURE__ */ jsx41(
                "polygon",
                {
                  points: areaPoints,
                  fill: chartColor,
                  fillOpacity: "0.1"
                }
              ),
              /* @__PURE__ */ jsx41(
                "polyline",
                {
                  points,
                  fill: "none",
                  stroke: chartColor,
                  strokeWidth: "1.5",
                  vectorEffect: "nonScalingStroke"
                }
              )
            ]
          }
        )
      }
    );
  }
);
ProbabilityChart.displayName = "ProbabilityChart";

// packages/ui/src/components/trading/bot-status.tsx
import * as React43 from "react";
import { jsx as jsx42, jsxs as jsxs37 } from "react/jsx-runtime";
var statusConfig = {
  online: { dot: "bg-[var(-ColorSuccess500)]", label: "Online" },
  degraded: { dot: "bg-[var(-ColorWarning500)]", label: "Degraded" },
  offline: { dot: "bg-[var(-ColorNeutral400)]", label: "Offline" }
};
var BotStatus = React43.forwardRef(
  ({ className, name, strategy, status, uptime, lastAction, ...props }, ref) => {
    const config = statusConfig[status];
    return /* @__PURE__ */ jsxs37(
      "div",
      {
        className: cn(
          "flex itemsCenter gap-[var(-Spacing4)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-BgPrimary)] p-[var(-Spacing4)]",
          className
        ),
        ref,
        ...props,
        children: [
          /* @__PURE__ */ jsxs37("div", { className: "relative", children: [
            /* @__PURE__ */ jsx42("span", { className: cn("block h3 w3 roundedFull", config.dot) }),
            status === "online" && /* @__PURE__ */ jsx42("span", { className: cn("absolute inset0 h3 w3 animatePing roundedFull opacity75", config.dot) })
          ] }),
          /* @__PURE__ */ jsxs37("div", { className: "flex flex1 flexCol", children: [
            /* @__PURE__ */ jsx42("span", { className: "text-[var(-FontSizeSm)] fontSemibold text-[var(-TextPrimary)]", children: name }),
            /* @__PURE__ */ jsx42("span", { className: "text-[var(-FontSizeXs)] text-[var(-TextTertiary)]", children: strategy })
          ] }),
          /* @__PURE__ */ jsxs37("div", { className: "flex flexCol itemsEnd", children: [
            /* @__PURE__ */ jsx42("span", { className: "text-[var(-FontSizeXs)] text-[var(-TextSecondary)]", children: uptime }),
            /* @__PURE__ */ jsx42("span", { className: "text-[var(-FontSizeXs)] text-[var(-TextTertiary)]", children: lastAction })
          ] })
        ]
      }
    );
  }
);
BotStatus.displayName = "BotStatus";

// packages/ui/src/components/data/quality-score.tsx
import * as React44 from "react";
import { jsx as jsx43, jsxs as jsxs38 } from "react/jsx-runtime";
var statusColor = { pass: "var(-StatusHealthy)", warn: "var(-StatusWarning)", fail: "var(-StatusError)" };
var QualityScore = React44.forwardRef(
  ({ className, dimensions, ...props }, ref) => /* @__PURE__ */ jsxs38("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
    /* @__PURE__ */ jsx43("div", { className: "mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Data Quality" }),
    /* @__PURE__ */ jsx43("div", { className: "flex flexCol gap-[var(-SpacingMd)]", children: dimensions.map((d, i) => /* @__PURE__ */ jsxs38("div", { className: "flex itemsCenter gap-[var(-SpacingMd)]", children: [
      /* @__PURE__ */ jsx43("span", { className: "w24 text-[var(-FontSm)] text-[var(-TextSecondary)]", children: d.name }),
      /* @__PURE__ */ jsx43("div", { className: "flex1 h2 roundedFull bg-[var(-BgTertiary)] overflowHidden", children: /* @__PURE__ */ jsx43("div", { className: "hFull roundedFull transitionAll", style: { width: `${d.score}%`, backgroundColor: statusColor[d.status] } }) }),
      /* @__PURE__ */ jsxs38("span", { className: "fontMono text-[var(-FontXs)] text-[var(-TextMuted)] w10 textRight", children: [
        d.score,
        "%"
      ] })
    ] }, i)) })
  ] })
);
QualityScore.displayName = "QualityScore";

// packages/ui/src/components/data/lineage-graph.tsx
import * as React45 from "react";
import { jsx as jsx44, jsxs as jsxs39 } from "react/jsx-runtime";
var typeColor = { source: "var(-ModelGemma)", transform: "var(-ModelDeepseek)", target: "var(-AccentTeal500)" };
var LineageGraph = React45.forwardRef(
  ({ className, nodes, edges, ...props }, ref) => /* @__PURE__ */ jsxs39("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
    /* @__PURE__ */ jsx44("div", { className: "mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Data Lineage" }),
    /* @__PURE__ */ jsx44("div", { className: "flex flexWrap gap-[var(-SpacingMd)]", children: nodes.map((node) => /* @__PURE__ */ jsxs39("div", { className: "flex itemsCenter gap-[var(-SpacingXs)] rounded-[var(-RadiusMd)] border border-[var(-BorderDefault)] bg-[var(-BgTertiary)] px-[var(-SpacingMd)] py-[var(-SpacingSm)]", children: [
      /* @__PURE__ */ jsx44("span", { className: "h2 w2 roundedFull", style: { backgroundColor: typeColor[node.type] } }),
      /* @__PURE__ */ jsx44("span", { className: "text-[var(-FontXs)] text-[var(-TextPrimary)]", children: node.name })
    ] }, node.id)) }),
    /* @__PURE__ */ jsxs39("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: [
      edges.length,
      " connections"
    ] })
  ] })
);
LineageGraph.displayName = "LineageGraph";

// packages/ui/src/components/data/metric-definition.tsx
import * as React46 from "react";
import { jsx as jsx45, jsxs as jsxs40 } from "react/jsx-runtime";
var MetricDefinition = React46.forwardRef(
  ({ className, name, definition, formula, owner, lastUpdated, ...props }, ref) => /* @__PURE__ */ jsxs40("div", { ref, className: cn("flex flexCol gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
    /* @__PURE__ */ jsx45("span", { className: "text-[var(-FontMd)] fontSemibold text-[var(-TextPrimary)]", children: name }),
    /* @__PURE__ */ jsx45("p", { className: "text-[var(-FontSm)] text-[var(-TextSecondary)]", children: definition }),
    /* @__PURE__ */ jsx45("code", { className: "rounded-[var(-RadiusSm)] bg-[var(-BgTertiary)] px-[var(-SpacingSm)] py-[var(-SpacingXs)] fontMono text-[var(-FontXs)] text-[var(-AccentTeal400)]", children: formula }),
    /* @__PURE__ */ jsxs40("div", { className: "flex itemsCenter justifyBetween borderT border-[var(-BorderDefault)] pt-[var(-SpacingSm)]", children: [
      /* @__PURE__ */ jsxs40("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: [
        "Owner: ",
        owner
      ] }),
      /* @__PURE__ */ jsx45("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: lastUpdated })
    ] })
  ] })
);
MetricDefinition.displayName = "MetricDefinition";

// packages/ui/src/components/data/pipeline-dag.tsx
import * as React47 from "react";
import { jsx as jsx46, jsxs as jsxs41 } from "react/jsx-runtime";
var nodeStatus = cva("flex h10 itemsCenter justifyCenter rounded-[var(-RadiusMd)] px-[var(-SpacingMd)] text-[var(-FontXs)] fontMedium border", {
  variants: {
    status: {
      running: "border-[var(-AccentTeal500)] bg-[var(-AccentTeal500)]/10 text-[var(-AccentTeal400)] animatePulse",
      success: "border-[var(-StatusHealthy)] bg-[var(-StatusHealthy)]/10 text-[var(-StatusHealthy)]",
      failed: "border-[var(-StatusError)] bg-[var(-StatusError)]/10 text-[var(-StatusError)]",
      pending: "border-[var(-BorderDefault)] bg-[var(-BgTertiary)] text-[var(-TextMuted)]"
    }
  },
  defaultVariants: { status: "pending" }
});
var PipelineDag = React47.forwardRef(
  ({ className, stages, ...props }, ref) => /* @__PURE__ */ jsxs41("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
    /* @__PURE__ */ jsx46("div", { className: "mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Pipeline DAG" }),
    /* @__PURE__ */ jsx46("div", { className: "flex itemsCenter gap-[var(-SpacingSm)]", children: stages.map((stage, si) => /* @__PURE__ */ jsxs41(React47.Fragment, { children: [
      /* @__PURE__ */ jsx46("div", { className: "flex flexCol gap-[var(-SpacingXs)]", children: stage.map((node) => /* @__PURE__ */ jsx46("div", { className: nodeStatus({ status: node.status }), children: node.name }, node.id)) }),
      si < stages.length - 1 && /* @__PURE__ */ jsx46("div", { className: "h0.5 w6 bg-[var(-BorderDefault)]" })
    ] }, si)) })
  ] })
);
PipelineDag.displayName = "PipelineDag";

// packages/ui/src/components/hr/perf-gauge.tsx
import * as React48 from "react";
import { jsx as jsx47, jsxs as jsxs42 } from "react/jsx-runtime";
var PerfGauge = React48.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs42("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx47("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Performance Gauge" }),
  /* @__PURE__ */ jsx47("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: label || "Component ready" })
] }));
PerfGauge.displayName = "PerfGauge";

// packages/ui/src/components/hr/candidate-card.tsx
import * as React49 from "react";
import { jsx as jsx48, jsxs as jsxs43 } from "react/jsx-runtime";
var CandidateCard = React49.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs43("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx48("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Candidate Card" }),
  /* @__PURE__ */ jsx48("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: label || "Component ready" })
] }));
CandidateCard.displayName = "CandidateCard";

// packages/ui/src/components/hr/org-node.tsx
import * as React50 from "react";
import { jsx as jsx49, jsxs as jsxs44 } from "react/jsx-runtime";
var OrgNode = React50.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs44("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx49("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Org Node" }),
  /* @__PURE__ */ jsx49("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: label || "Component ready" })
] }));
OrgNode.displayName = "OrgNode";

// packages/ui/src/components/care/ticket-card.tsx
import * as React51 from "react";
import { jsx as jsx50, jsxs as jsxs45 } from "react/jsx-runtime";
var TicketCard = React51.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs45("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx50("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Ticket" }),
  /* @__PURE__ */ jsx50("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: label || "Component ready" })
] }));
TicketCard.displayName = "TicketCard";

// packages/ui/src/components/care/sla-tracker.tsx
import * as React52 from "react";
import { jsx as jsx51, jsxs as jsxs46 } from "react/jsx-runtime";
var SlaTracker = React52.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs46("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx51("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "SLA" }),
  /* @__PURE__ */ jsx51("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: label || "Component ready" })
] }));
SlaTracker.displayName = "SlaTracker";

// packages/ui/src/components/cs/nps-gauge.tsx
import * as React53 from "react";
import { jsx as jsx52, jsxs as jsxs47 } from "react/jsx-runtime";
var NpsGauge = React53.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs47("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx52("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "NPS" }),
  /* @__PURE__ */ jsx52("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: label || "Component ready" })
] }));
NpsGauge.displayName = "NpsGauge";

// packages/ui/src/components/cs/health-score.tsx
import * as React54 from "react";
import { jsx as jsx53, jsxs as jsxs48 } from "react/jsx-runtime";
var HealthScore = React54.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs48("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx53("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Health Score" }),
  /* @__PURE__ */ jsx53("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: label || "Component ready" })
] }));
HealthScore.displayName = "HealthScore";

// packages/ui/src/components/cs/churn-risk.tsx
import * as React55 from "react";
import { jsx as jsx54, jsxs as jsxs49 } from "react/jsx-runtime";
var ChurnRisk = React55.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs49("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx54("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Churn Risk" }),
  /* @__PURE__ */ jsx54("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: label || "Component ready" })
] }));
ChurnRisk.displayName = "ChurnRisk";

// packages/ui/src/components/cdp/segment-builder.tsx
import * as React56 from "react";
import { jsx as jsx55, jsxs as jsxs50 } from "react/jsx-runtime";
var SegmentBuilder = React56.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs50("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx55("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Segment Builder" }),
  /* @__PURE__ */ jsx55("p", { className: "mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: "Dynamic segment criteria builder" }),
  /* @__PURE__ */ jsx55("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]", children: label || "Ready" })
] }));
SegmentBuilder.displayName = "SegmentBuilder";

// packages/ui/src/components/cdp/customer-360.tsx
import * as React57 from "react";
import { jsx as jsx56, jsxs as jsxs51 } from "react/jsx-runtime";
var Customer360 = React57.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs51("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx56("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Customer 360" }),
  /* @__PURE__ */ jsx56("p", { className: "mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: "Unified customer profile view" }),
  /* @__PURE__ */ jsx56("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]", children: label || "Ready" })
] }));
Customer360.displayName = "Customer360";

// packages/ui/src/components/cdp/journey-map.tsx
import * as React58 from "react";
import { jsx as jsx57, jsxs as jsxs52 } from "react/jsx-runtime";
var JourneyMap = React58.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs52("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx57("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Journey Map" }),
  /* @__PURE__ */ jsx57("p", { className: "mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: "Customer journey stage visualization" }),
  /* @__PURE__ */ jsx57("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]", children: label || "Ready" })
] }));
JourneyMap.displayName = "JourneyMap";

// packages/ui/src/components/pm/pipeline-funnel.tsx
import * as React59 from "react";
import { jsx as jsx58, jsxs as jsxs53 } from "react/jsx-runtime";
var PipelineFunnel = React59.forwardRef(
  ({ className, stages, ...props }, ref) => {
    const max = Math.max(...stages.map((s) => s.value), 1);
    return /* @__PURE__ */ jsxs53("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
      /* @__PURE__ */ jsx58("div", { className: "mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Revenue Funnel" }),
      /* @__PURE__ */ jsx58("div", { className: "flex flexCol gap-[var(-SpacingSm)]", children: stages.map((stage, i) => {
        const width = Math.round(stage.value / max * 100);
        return /* @__PURE__ */ jsxs53("div", { className: "flex itemsCenter gap-[var(-SpacingMd)]", children: [
          /* @__PURE__ */ jsx58("span", { className: "w20 text-[var(-FontXs)] text-[var(-TextSecondary)] textRight", children: stage.name }),
          /* @__PURE__ */ jsx58("div", { className: "flex1 h6 rounded-[var(-RadiusSm)] bg-[var(-BgTertiary)] overflowHidden", children: /* @__PURE__ */ jsx58("div", { className: "hFull rounded-[var(-RadiusSm)] bg-[var(-AccentTeal500)]/60 flex itemsCenter px2 transitionAll", style: { width: `${width}%` }, children: /* @__PURE__ */ jsxs53("span", { className: "fontMono text-[var(-FontXs)] text-[var(-TextPrimary)]", children: [
            "$",
            (stage.value / 1e3).toFixed(0),
            "K"
          ] }) }) }),
          /* @__PURE__ */ jsx58("span", { className: "fontMono text-[var(-FontXs)] text-[var(-TextMuted)] w8 textRight", children: stage.count })
        ] }, i);
      }) })
    ] });
  }
);
PipelineFunnel.displayName = "PipelineFunnel";

// packages/ui/src/components/pm/experiment-card.tsx
import * as React60 from "react";
import { jsx as jsx59, jsxs as jsxs54 } from "react/jsx-runtime";
var resultBadge = cva("rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontMedium", {
  variants: {
    result: {
      winning: "bg-[var(-StatusHealthy)]/15 text-[var(-StatusHealthy)]",
      losing: "bg-[var(-StatusError)]/15 text-[var(-StatusError)]",
      inconclusive: "bg-[var(-StatusWarning)]/15 text-[var(-StatusWarning)]",
      running: "bg-[var(-ModelQwen)]/15 text-[var(-ModelQwen)]"
    }
  },
  defaultVariants: { result: "running" }
});
var ExperimentCard = React60.forwardRef(
  ({ className, name, hypothesis, variant, confidence, result, sampleSize, ...props }, ref) => /* @__PURE__ */ jsxs54("div", { ref, className: cn("flex flexCol gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
    /* @__PURE__ */ jsxs54("div", { className: "flex itemsCenter justifyBetween", children: [
      /* @__PURE__ */ jsx59("span", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: name }),
      /* @__PURE__ */ jsx59("span", { className: resultBadge({ result }), children: result })
    ] }),
    /* @__PURE__ */ jsx59("p", { className: "text-[var(-FontXs)] text-[var(-TextSecondary)]", children: hypothesis }),
    /* @__PURE__ */ jsxs54("div", { className: "flex itemsCenter gap-[var(-SpacingLg)] borderT border-[var(-BorderDefault)] pt-[var(-SpacingSm)] text-[var(-FontXs)]", children: [
      /* @__PURE__ */ jsxs54("span", { className: "text-[var(-TextMuted)]", children: [
        "Variant: ",
        variant
      ] }),
      /* @__PURE__ */ jsxs54("span", { className: "text-[var(-TextMuted)]", children: [
        "n=",
        sampleSize.toLocaleString()
      ] }),
      /* @__PURE__ */ jsxs54("span", { className: "fontMono text-[var(-AccentTeal400)]", children: [
        confidence,
        "% confidence"
      ] })
    ] })
  ] })
);
ExperimentCard.displayName = "ExperimentCard";

// packages/ui/src/components/pm/roadmap-lane.tsx
import * as React61 from "react";
import { jsx as jsx60, jsxs as jsxs55 } from "react/jsx-runtime";
var laneBg = cva("rounded-[var(-RadiusLg)] border p-[var(-SpacingLg)]", {
  variants: {
    lane: {
      now: "border-[var(-StatusHealthy)]/30 bg-[var(-StatusHealthy)]/5",
      next: "border-[var(-StatusWarning)]/30 bg-[var(-StatusWarning)]/5",
      later: "border-[var(-BorderDefault)] bg-[var(-SurfaceCard)]"
    }
  },
  defaultVariants: { lane: "later" }
});
var RoadmapLane = React61.forwardRef(
  ({ className, lane, items, ...props }, ref) => /* @__PURE__ */ jsxs55("div", { ref, className: cn(laneBg({ lane }), className), ...props, children: [
    /* @__PURE__ */ jsx60("div", { className: "mb-[var(-SpacingMd)] text-[var(-FontSm)] fontBold uppercase trackingWider text-[var(-TextSecondary)]", children: lane }),
    /* @__PURE__ */ jsx60("div", { className: "flex flexCol gap-[var(-SpacingSm)]", children: items.map((item, i) => /* @__PURE__ */ jsxs55("div", { className: "flex itemsCenter justifyBetween rounded-[var(-RadiusMd)] bg-[var(-BgPrimary)]/50 px-[var(-SpacingMd)] py-[var(-SpacingSm)]", children: [
      /* @__PURE__ */ jsx60("span", { className: "text-[var(-FontSm)] text-[var(-TextPrimary)]", children: item.title }),
      /* @__PURE__ */ jsxs55("div", { className: "flex itemsCenter gap-[var(-SpacingSm)]", children: [
        /* @__PURE__ */ jsx60("span", { className: "rounded-[var(-RadiusSm)] bg-[var(-BgTertiary)] px1.5 py0.5 text-[var(-FontXs)] text-[var(-TextMuted)]", children: item.tag }),
        /* @__PURE__ */ jsx60("span", { className: "fontMono text-[var(-FontXs)] text-[var(-AccentTeal400)]", children: item.score })
      ] })
    ] }, i)) })
  ] })
);
RoadmapLane.displayName = "RoadmapLane";

// packages/ui/src/components/pm/feature-flag.tsx
import * as React62 from "react";
import { jsx as jsx61, jsxs as jsxs56 } from "react/jsx-runtime";
var FeatureFlag = React62.forwardRef(
  ({ className, name, enabled, rolloutPct, environment, ...props }, ref) => /* @__PURE__ */ jsxs56("div", { ref, className: cn("flex itemsCenter justifyBetween rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] px-[var(-SpacingLg)] py-[var(-SpacingMd)]", className), ...props, children: [
    /* @__PURE__ */ jsxs56("div", { className: "flex itemsCenter gap-[var(-SpacingMd)]", children: [
      /* @__PURE__ */ jsx61("div", { className: cn("h3 w3 roundedFull", enabled ? "bg-[var(-StatusHealthy)]" : "bg-[var(-StatusIdle)]") }),
      /* @__PURE__ */ jsx61("span", { className: "fontMono text-[var(-FontSm)] text-[var(-TextPrimary)]", children: name })
    ] }),
    /* @__PURE__ */ jsxs56("div", { className: "flex itemsCenter gap-[var(-SpacingLg)]", children: [
      /* @__PURE__ */ jsx61("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: environment }),
      /* @__PURE__ */ jsxs56("div", { className: "flex itemsCenter gap-[var(-SpacingSm)]", children: [
        /* @__PURE__ */ jsx61("div", { className: "h1.5 w20 overflowHidden roundedFull bg-[var(-BgTertiary)]", children: /* @__PURE__ */ jsx61("div", { className: "hFull roundedFull bg-[var(-AccentTeal500)]", style: { width: `${rolloutPct}%` } }) }),
        /* @__PURE__ */ jsxs56("span", { className: "fontMono text-[var(-FontXs)] text-[var(-TextSecondary)]", children: [
          rolloutPct,
          "%"
        ] })
      ] })
    ] })
  ] })
);
FeatureFlag.displayName = "FeatureFlag";

// packages/ui/src/components/pm/attribution-chart.tsx
import * as React63 from "react";
import { jsx as jsx62, jsxs as jsxs57 } from "react/jsx-runtime";
var AttributionChart = React63.forwardRef(
  ({ className, channels, ...props }, ref) => {
    const maxRevenue = Math.max(...channels.map((c) => c.revenue), 1);
    return /* @__PURE__ */ jsxs57("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
      /* @__PURE__ */ jsx62("div", { className: "mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "MultiTouch Attribution" }),
      /* @__PURE__ */ jsx62("div", { className: "flex flexCol gap-[var(-SpacingSm)]", children: channels.map((ch, i) => /* @__PURE__ */ jsxs57("div", { className: "flex itemsCenter gap-[var(-SpacingMd)]", children: [
        /* @__PURE__ */ jsx62("span", { className: "w20 text-[var(-FontXs)] text-[var(-TextSecondary)] truncate", children: ch.channel }),
        /* @__PURE__ */ jsx62("div", { className: "flex1 h4 rounded-[var(-RadiusSm)] bg-[var(-BgTertiary)] overflowHidden", children: /* @__PURE__ */ jsx62("div", { className: "hFull rounded-[var(-RadiusSm)] bg-[var(-ModelGemma)]/60", style: { width: `${ch.revenue / maxRevenue * 100}%` } }) }),
        /* @__PURE__ */ jsxs57("span", { className: "fontMono text-[var(-FontXs)] text-[var(-TextMuted)] w16 textRight", children: [
          ch.roi.toFixed(1),
          "x ROI"
        ] })
      ] }, i)) })
    ] });
  }
);
AttributionChart.displayName = "AttributionChart";

// packages/ui/src/components/ipo/milestone-track.tsx
import * as React64 from "react";
import { jsx as jsx63, jsxs as jsxs58 } from "react/jsx-runtime";
var phaseStatus = cva("flex h8 w8 itemsCenter justifyCenter roundedFull text-[var(-FontXs)] fontBold", {
  variants: { status: { done: "bg-[var(-StatusHealthy)] text-[var(-BgPrimary)]", active: "bg-[var(-AccentTeal500)] text-[var(-BgPrimary)] animatePulse", pending: "bg-[var(-BgTertiary)] text-[var(-TextMuted)]" } },
  defaultVariants: { status: "pending" }
});
var MilestoneTrack = React64.forwardRef(({ className, milestones, ...props }, ref) => /* @__PURE__ */ jsxs58("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx63("div", { className: "mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "IPO Milestones" }),
  /* @__PURE__ */ jsx63("div", { className: "flex itemsCenter", children: milestones.map((m, i) => /* @__PURE__ */ jsxs58(React64.Fragment, { children: [
    /* @__PURE__ */ jsxs58("div", { className: "flex flexCol itemsCenter gap-[var(-SpacingXs)]", children: [
      /* @__PURE__ */ jsx63("span", { className: phaseStatus({ status: m.status }), children: m.status === "done" ? "\u2713" : i + 1 }),
      /* @__PURE__ */ jsx63("span", { className: "text-[var(-FontXs)] text-[var(-TextSecondary)] whitespaceNowrap", children: m.name }),
      /* @__PURE__ */ jsx63("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: m.date })
    ] }),
    i < milestones.length - 1 && /* @__PURE__ */ jsx63("div", { className: cn("h0.5 flex1 mx1 minW-[16px]", m.status === "done" ? "bg-[var(-StatusHealthy)]" : "bg-[var(-BorderDefault)]") })
  ] }, i)) })
] }));
MilestoneTrack.displayName = "MilestoneTrack";

// packages/ui/src/components/ipo/filing-status.tsx
import * as React65 from "react";
import { jsx as jsx64, jsxs as jsxs59 } from "react/jsx-runtime";
var statusBadge = cva("rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontMedium", {
  variants: { status: { filed: "bg-[var(-StatusHealthy)]/15 text-[var(-StatusHealthy)]", drafting: "bg-[var(-StatusWarning)]/15 text-[var(-StatusWarning)]", "notStarted": "bg-[var(-StatusIdle)]/15 text-[var(-StatusIdle)]" } },
  defaultVariants: { status: "notStarted" }
});
var FilingStatus = React65.forwardRef(({ className, filings, ...props }, ref) => /* @__PURE__ */ jsxs59("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] overflowHidden", className), ...props, children: [
  /* @__PURE__ */ jsx64("div", { className: "borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)]", children: /* @__PURE__ */ jsx64("span", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "SEC Filings" }) }),
  filings.map((f, i) => /* @__PURE__ */ jsxs59("div", { className: "flex itemsCenter justifyBetween borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingMd)] last:borderB0 hover:bg-[var(-SurfaceHover)]", children: [
    /* @__PURE__ */ jsx64("span", { className: "text-[var(-FontSm)] text-[var(-TextPrimary)]", children: f.name }),
    /* @__PURE__ */ jsxs59("div", { className: "flex itemsCenter gap-[var(-SpacingMd)]", children: [
      /* @__PURE__ */ jsx64("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: f.deadline }),
      /* @__PURE__ */ jsx64("span", { className: statusBadge({ status: f.status }), children: f.status })
    ] })
  ] }, i))
] }));
FilingStatus.displayName = "FilingStatus";

// packages/ui/src/components/ipo/readiness-score.tsx
import * as React66 from "react";
import { jsx as jsx65, jsxs as jsxs60 } from "react/jsx-runtime";
var ReadinessScore = React66.forwardRef(({ className, overall, categories, target, ...props }, ref) => /* @__PURE__ */ jsxs60("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsxs60("div", { className: "flex itemsCenter justifyBetween mb-[var(-SpacingMd)]", children: [
    /* @__PURE__ */ jsx65("span", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "IPO Readiness" }),
    /* @__PURE__ */ jsxs60("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: [
      "Target: ",
      target,
      "%"
    ] })
  ] }),
  /* @__PURE__ */ jsxs60("div", { className: cn("fontMono text-[var(-Font3xl)] fontBold", overall >= target ? "text-[var(-StatusHealthy)]" : "text-[var(-StatusWarning)]"), children: [
    overall,
    "%"
  ] }),
  /* @__PURE__ */ jsx65("div", { className: "mt-[var(-SpacingMd)] flex flexCol gap-[var(-SpacingXs)]", children: categories.map((c, i) => /* @__PURE__ */ jsxs60("div", { className: "flex itemsCenter gap-[var(-SpacingSm)]", children: [
    /* @__PURE__ */ jsx65("span", { className: "w24 text-[var(-FontXs)] text-[var(-TextSecondary)]", children: c.name }),
    /* @__PURE__ */ jsx65("div", { className: "flex1 h1.5 roundedFull bg-[var(-BgTertiary)] overflowHidden", children: /* @__PURE__ */ jsx65("div", { className: "hFull roundedFull bg-[var(-AccentTeal500)]", style: { width: `${c.score}%` } }) }),
    /* @__PURE__ */ jsxs60("span", { className: "fontMono text-[var(-FontXs)] text-[var(-TextMuted)] w8 textRight", children: [
      c.score,
      "%"
    ] })
  ] }, i)) })
] }));
ReadinessScore.displayName = "ReadinessScore";

// packages/ui/src/components/legal/compliance-status.tsx
import * as React67 from "react";
import { jsx as jsx66, jsxs as jsxs61 } from "react/jsx-runtime";
var ComplianceStatus = React67.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs61("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx66("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Compliance Status" }),
  /* @__PURE__ */ jsx66("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: label || "Component ready" })
] }));
ComplianceStatus.displayName = "ComplianceStatus";

// packages/ui/src/components/legal/contract-card.tsx
import * as React68 from "react";
import { jsx as jsx67, jsxs as jsxs62 } from "react/jsx-runtime";
var ContractCard = React68.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs62("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx67("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Contract Card" }),
  /* @__PURE__ */ jsx67("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: label || "Component ready" })
] }));
ContractCard.displayName = "ContractCard";

// packages/ui/src/components/ml/model-card.tsx
import * as React69 from "react";
import { jsx as jsx68, jsxs as jsxs63 } from "react/jsx-runtime";
var modelStatusBadge = cva("rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontMedium", {
  variants: {
    status: {
      serving: "bg-[var(-StatusHealthy)]/15 text-[var(-StatusHealthy)]",
      canary: "bg-[var(-StatusWarning)]/15 text-[var(-StatusWarning)]",
      shadow: "bg-[var(-ModelDeepseek)]/15 text-[var(-ModelDeepseek)]",
      retired: "bg-[var(-StatusIdle)]/15 text-[var(-StatusIdle)]"
    }
  },
  defaultVariants: { status: "serving" }
});
var ModelCard = React69.forwardRef(
  ({ className, name, version, status, latencyP99, costPer1k, driftScore, ...props }, ref) => /* @__PURE__ */ jsxs63("div", { ref, className: cn("flex flexCol gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
    /* @__PURE__ */ jsxs63("div", { className: "flex itemsCenter justifyBetween", children: [
      /* @__PURE__ */ jsxs63("div", { className: "flex itemsCenter gap-[var(-SpacingSm)]", children: [
        /* @__PURE__ */ jsx68("span", { className: "text-[var(-FontMd)] fontSemibold text-[var(-TextPrimary)]", children: name }),
        /* @__PURE__ */ jsxs63("span", { className: "fontMono text-[var(-FontXs)] text-[var(-TextMuted)]", children: [
          "v",
          version
        ] })
      ] }),
      /* @__PURE__ */ jsx68("span", { className: modelStatusBadge({ status }), children: status })
    ] }),
    /* @__PURE__ */ jsxs63("div", { className: "grid gridCols3 gap-[var(-SpacingMd)] borderT border-[var(-BorderDefault)] pt-[var(-SpacingSm)]", children: [
      /* @__PURE__ */ jsxs63("div", { className: "flex flexCol", children: [
        /* @__PURE__ */ jsx68("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: "P99 Latency" }),
        /* @__PURE__ */ jsxs63("span", { className: "fontMono text-[var(-FontSm)] text-[var(-TextPrimary)]", children: [
          latencyP99,
          "ms"
        ] })
      ] }),
      /* @__PURE__ */ jsxs63("div", { className: "flex flexCol", children: [
        /* @__PURE__ */ jsx68("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: "Cost/1K" }),
        /* @__PURE__ */ jsxs63("span", { className: "fontMono text-[var(-FontSm)] text-[var(-TextPrimary)]", children: [
          "$",
          costPer1k.toFixed(3)
        ] })
      ] }),
      /* @__PURE__ */ jsxs63("div", { className: "flex flexCol", children: [
        /* @__PURE__ */ jsx68("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: "Drift" }),
        /* @__PURE__ */ jsx68("span", { className: cn("fontMono text-[var(-FontSm)]", driftScore > 0.1 ? "text-[var(-StatusError)]" : "text-[var(-StatusHealthy)]"), children: driftScore.toFixed(3) })
      ] })
    ] })
  ] })
);
ModelCard.displayName = "ModelCard";

// packages/ui/src/components/ml/eval-suite.tsx
import * as React70 from "react";
import { jsx as jsx69, jsxs as jsxs64 } from "react/jsx-runtime";
var EvalSuite = React70.forwardRef(
  ({ className, results, ...props }, ref) => {
    const passCount = results.filter((r2) => r2.passed).length;
    return /* @__PURE__ */ jsxs64("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] overflowHidden", className), ...props, children: [
      /* @__PURE__ */ jsxs64("div", { className: "flex itemsCenter justifyBetween borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)]", children: [
        /* @__PURE__ */ jsx69("span", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Eval Suite" }),
        /* @__PURE__ */ jsxs64("span", { className: "fontMono text-[var(-FontXs)] text-[var(-TextMuted)]", children: [
          passCount,
          "/",
          results.length,
          " passed"
        ] })
      ] }),
      results.map((r2, i) => /* @__PURE__ */ jsxs64("div", { className: "flex itemsCenter justifyBetween borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)] last:borderB0 hover:bg-[var(-SurfaceHover)]", children: [
        /* @__PURE__ */ jsxs64("div", { className: "flex itemsCenter gap-[var(-SpacingSm)]", children: [
          /* @__PURE__ */ jsx69("span", { className: cn("fontBold", r2.passed ? "text-[var(-StatusHealthy)]" : "text-[var(-StatusError)]"), children: r2.passed ? "\u2713" : "\u2717" }),
          /* @__PURE__ */ jsx69("span", { className: "text-[var(-FontSm)] text-[var(-TextPrimary)]", children: r2.name })
        ] }),
        /* @__PURE__ */ jsxs64("div", { className: "flex itemsCenter gap-[var(-SpacingMd)] fontMono text-[var(-FontXs)]", children: [
          /* @__PURE__ */ jsxs64("span", { className: "text-[var(-TextMuted)]", children: [
            "baseline: ",
            r2.baseline.toFixed(2)
          ] }),
          /* @__PURE__ */ jsx69("span", { className: cn(r2.score >= r2.baseline ? "text-[var(-StatusHealthy)]" : "text-[var(-StatusError)]"), children: r2.score.toFixed(2) })
        ] })
      ] }, i))
    ] });
  }
);
EvalSuite.displayName = "EvalSuite";

// packages/ui/src/components/ml/cost-tracker.tsx
import * as React71 from "react";
import { jsx as jsx70, jsxs as jsxs65 } from "react/jsx-runtime";
var CostTracker = React71.forwardRef(
  ({ className, models, budget, ...props }, ref) => {
    const totalCost = models.reduce((sum, m) => sum + m.cost, 0);
    const pct = Math.round(totalCost / budget * 100);
    return /* @__PURE__ */ jsxs65("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
      /* @__PURE__ */ jsxs65("div", { className: "flex itemsCenter justifyBetween mb-[var(-SpacingMd)]", children: [
        /* @__PURE__ */ jsx70("span", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Inference Cost" }),
        /* @__PURE__ */ jsxs65("span", { className: cn("fontMono text-[var(-FontSm)]", pct > 90 ? "text-[var(-StatusError)]" : "text-[var(-TextSecondary)]"), children: [
          "$",
          totalCost.toFixed(2),
          " / $",
          budget
        ] })
      ] }),
      /* @__PURE__ */ jsx70("div", { className: "h3 wFull overflowHidden roundedFull bg-[var(-BgTertiary)] mb-[var(-SpacingMd)]", children: /* @__PURE__ */ jsx70("div", { className: cn("hFull roundedFull transitionAll", pct > 90 ? "bg-[var(-StatusError)]" : pct > 70 ? "bg-[var(-StatusWarning)]" : "bg-[var(-AccentTeal500)]"), style: { width: `${Math.min(pct, 100)}%` } }) }),
      /* @__PURE__ */ jsx70("div", { className: "flex flexCol gap-[var(-SpacingXs)]", children: models.map((m, i) => /* @__PURE__ */ jsxs65("div", { className: "flex itemsCenter justifyBetween text-[var(-FontXs)]", children: [
        /* @__PURE__ */ jsxs65("div", { className: "flex itemsCenter gap-[var(-SpacingSm)]", children: [
          /* @__PURE__ */ jsx70("span", { className: "h2 w2 roundedFull", style: { backgroundColor: m.color } }),
          /* @__PURE__ */ jsx70("span", { className: "text-[var(-TextPrimary)]", children: m.model })
        ] }),
        /* @__PURE__ */ jsxs65("div", { className: "flex itemsCenter gap-[var(-SpacingLg)]", children: [
          /* @__PURE__ */ jsxs65("span", { className: "text-[var(-TextMuted)]", children: [
            m.requests.toLocaleString(),
            " req"
          ] }),
          /* @__PURE__ */ jsxs65("span", { className: "fontMono text-[var(-TextSecondary)]", children: [
            "$",
            m.cost.toFixed(2)
          ] })
        ] })
      ] }, i)) })
    ] });
  }
);
CostTracker.displayName = "CostTracker";

// packages/ui/src/components/ml/guardrail-log.tsx
import * as React72 from "react";
import { jsx as jsx71, jsxs as jsxs66 } from "react/jsx-runtime";
var triggerBadge = cva("rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontMedium", {
  variants: {
    action: {
      blocked: "bg-[var(-StatusError)]/15 text-[var(-StatusError)]",
      flagged: "bg-[var(-StatusWarning)]/15 text-[var(-StatusWarning)]",
      passed: "bg-[var(-StatusHealthy)]/15 text-[var(-StatusHealthy)]"
    }
  },
  defaultVariants: { action: "passed" }
});
var GuardrailLog = React72.forwardRef(
  ({ className, events, ...props }, ref) => /* @__PURE__ */ jsxs66("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] overflowHidden", className), ...props, children: [
    /* @__PURE__ */ jsx71("div", { className: "borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)]", children: /* @__PURE__ */ jsx71("span", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Guardrail Log" }) }),
    /* @__PURE__ */ jsx71("div", { className: "maxH64 overflowYAuto", children: events.map((e, i) => /* @__PURE__ */ jsxs66("div", { className: "flex itemsCenter gap-[var(-SpacingMd)] borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)] last:borderB0", children: [
      /* @__PURE__ */ jsx71("span", { className: "fontMono text-[var(-FontXs)] text-[var(-TextMuted)] minW-[48px]", children: e.time }),
      /* @__PURE__ */ jsx71("span", { className: triggerBadge({ action: e.action }), children: e.action }),
      /* @__PURE__ */ jsx71("span", { className: "text-[var(-FontXs)] text-[var(-TextSecondary)]", children: e.rule }),
      /* @__PURE__ */ jsx71("span", { className: "flex1 truncate text-[var(-FontXs)] text-[var(-TextMuted)]", children: e.input })
    ] }, i)) })
  ] })
);
GuardrailLog.displayName = "GuardrailLog";

// packages/ui/src/components/obs/metric-card.tsx
import * as React73 from "react";
import { jsx as jsx72, jsxs as jsxs67 } from "react/jsx-runtime";
var MetricCard = React73.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs67("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx72("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Metric Card" }),
  /* @__PURE__ */ jsx72("p", { className: "mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: "Single metric with sparkline and threshold" }),
  /* @__PURE__ */ jsx72("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]", children: label || "Ready" })
] }));
MetricCard.displayName = "MetricCard";

// packages/ui/src/components/obs/log-viewer.tsx
import * as React74 from "react";
import { jsx as jsx73, jsxs as jsxs68 } from "react/jsx-runtime";
var LogViewer = React74.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs68("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx73("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Log Viewer" }),
  /* @__PURE__ */ jsx73("p", { className: "mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: "Structured log stream viewer" }),
  /* @__PURE__ */ jsx73("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]", children: label || "Ready" })
] }));
LogViewer.displayName = "LogViewer";

// packages/ui/src/components/obs/alert-rule.tsx
import * as React75 from "react";
import { jsx as jsx74, jsxs as jsxs69 } from "react/jsx-runtime";
var AlertRule = React75.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs69("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx74("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Alert Rule" }),
  /* @__PURE__ */ jsx74("p", { className: "mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: "Alert rule with condition and routing" }),
  /* @__PURE__ */ jsx74("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]", children: label || "Ready" })
] }));
AlertRule.displayName = "AlertRule";

// packages/ui/src/components/obs/trace-waterfall.tsx
import * as React76 from "react";
import { jsx as jsx75, jsxs as jsxs70 } from "react/jsx-runtime";
var TraceWaterfall = React76.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs70("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx75("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Trace Waterfall" }),
  /* @__PURE__ */ jsx75("p", { className: "mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: "Distributed trace timeline visualization" }),
  /* @__PURE__ */ jsx75("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]", children: label || "Ready" })
] }));
TraceWaterfall.displayName = "TraceWaterfall";

// packages/ui/src/components/audit/control-card.tsx
import * as React77 from "react";
import { jsx as jsx76, jsxs as jsxs71 } from "react/jsx-runtime";
var testStatusVariants = cva("inlineFlex itemsCenter rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontMedium", {
  variants: {
    status: {
      passed: "bg-[var(-StatusHealthy)]/15 text-[var(-StatusHealthy)]",
      failed: "bg-[var(-StatusError)]/15 text-[var(-StatusError)]",
      pending: "bg-[var(-StatusWarning)]/15 text-[var(-StatusWarning)]",
      "notTested": "bg-[var(-StatusIdle)]/15 text-[var(-StatusIdle)]"
    }
  },
  defaultVariants: { status: "notTested" }
});
var ControlCard = React77.forwardRef(
  ({ className, controlId, name, owner, testStatus, lastTested, ...props }, ref) => /* @__PURE__ */ jsxs71("div", { ref, className: cn("flex itemsCenter justifyBetween rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] px-[var(-SpacingLg)] py-[var(-SpacingMd)]", className), ...props, children: [
    /* @__PURE__ */ jsxs71("div", { className: "flex flexCol gap-[var(-SpacingXs)]", children: [
      /* @__PURE__ */ jsxs71("div", { className: "flex itemsCenter gap-[var(-SpacingSm)]", children: [
        /* @__PURE__ */ jsx76("span", { className: "fontMono text-[var(-FontXs)] text-[var(-TextMuted)]", children: controlId }),
        /* @__PURE__ */ jsx76("span", { className: "text-[var(-FontSm)] fontMedium text-[var(-TextPrimary)]", children: name })
      ] }),
      /* @__PURE__ */ jsxs71("span", { className: "text-[var(-FontXs)] text-[var(-TextSecondary)]", children: [
        "Owner: ",
        owner
      ] })
    ] }),
    /* @__PURE__ */ jsxs71("div", { className: "flex itemsCenter gap-[var(-SpacingMd)]", children: [
      lastTested && /* @__PURE__ */ jsx76("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: lastTested }),
      /* @__PURE__ */ jsx76("span", { className: testStatusVariants({ status: testStatus }), children: testStatus })
    ] })
  ] })
);
ControlCard.displayName = "ControlCard";

// packages/ui/src/components/audit/sox-progress.tsx
import * as React78 from "react";
import { jsx as jsx77, jsxs as jsxs72 } from "react/jsx-runtime";
var SoxProgress = React78.forwardRef(
  ({ className, phases, ...props }, ref) => /* @__PURE__ */ jsxs72("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
    /* @__PURE__ */ jsx77("div", { className: "mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "SOX ICFR Progress" }),
    /* @__PURE__ */ jsx77("div", { className: "flex flexCol gap-[var(-SpacingMd)]", children: phases.map((phase, i) => {
      const pct = phase.total > 0 ? Math.round(phase.completed / phase.total * 100) : 0;
      return /* @__PURE__ */ jsxs72("div", { className: "flex flexCol gap-[var(-SpacingXs)]", children: [
        /* @__PURE__ */ jsxs72("div", { className: "flex itemsCenter justifyBetween", children: [
          /* @__PURE__ */ jsx77("span", { className: "text-[var(-FontSm)] text-[var(-TextPrimary)]", children: phase.name }),
          /* @__PURE__ */ jsxs72("span", { className: "fontMono text-[var(-FontXs)] text-[var(-TextMuted)]", children: [
            phase.completed,
            "/",
            phase.total
          ] })
        ] }),
        /* @__PURE__ */ jsx77("div", { className: "h2 wFull overflowHidden roundedFull bg-[var(-BgTertiary)]", children: /* @__PURE__ */ jsx77("div", { className: "hFull roundedFull bg-[var(-AccentTeal500)] transitionAll duration500", style: { width: `${pct}%` } }) })
      ] }, i);
    }) })
  ] })
);
SoxProgress.displayName = "SoxProgress";

// packages/ui/src/components/audit/risk-heatmap.tsx
import * as React79 from "react";
import { jsx as jsx78, jsxs as jsxs73 } from "react/jsx-runtime";
var cellColors = [
  ["bg-[var(-StatusHealthy)]/20", "bg-[var(-StatusHealthy)]/30", "bg-[var(-StatusWarning)]/20", "bg-[var(-StatusWarning)]/30", "bg-[var(-StatusError)]/20"],
  ["bg-[var(-StatusHealthy)]/30", "bg-[var(-StatusWarning)]/20", "bg-[var(-StatusWarning)]/30", "bg-[var(-StatusError)]/20", "bg-[var(-StatusError)]/30"],
  ["bg-[var(-StatusWarning)]/20", "bg-[var(-StatusWarning)]/30", "bg-[var(-StatusError)]/20", "bg-[var(-StatusError)]/30", "bg-[var(-StatusError)]/40"],
  ["bg-[var(-StatusWarning)]/30", "bg-[var(-StatusError)]/20", "bg-[var(-StatusError)]/30", "bg-[var(-StatusError)]/40", "bg-[var(-StatusError)]/60"],
  ["bg-[var(-StatusError)]/20", "bg-[var(-StatusError)]/30", "bg-[var(-StatusError)]/40", "bg-[var(-StatusError)]/60", "bg-[var(-StatusError)]/80"]
];
var RiskHeatmap = React79.forwardRef(
  ({ className, data, ...props }, ref) => /* @__PURE__ */ jsxs73("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
    /* @__PURE__ */ jsx78("div", { className: "mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Risk Heat Map" }),
    /* @__PURE__ */ jsx78("div", { className: "grid gridCols5 gap1", children: [4, 3, 2, 1, 0].map(
      (row) => [0, 1, 2, 3, 4].map((col) => {
        const items = data.filter((d) => d.likelihood === col + 1 && d.impact === row + 1);
        return /* @__PURE__ */ jsx78("div", { className: cn("flex h12 itemsCenter justifyCenter rounded-[var(-RadiusSm)] text-[var(-FontXs)] text-[var(-TextPrimary)]", cellColors[row][col]), children: items.map((item) => item.label).join(", ") }, `${row}-${col}`);
      })
    ) }),
    /* @__PURE__ */ jsxs73("div", { className: "mt-[var(-SpacingXs)] flex justifyBetween text-[var(-FontXs)] text-[var(-TextMuted)]", children: [
      /* @__PURE__ */ jsx78("span", { children: "Low Likelihood" }),
      /* @__PURE__ */ jsx78("span", { children: "High Likelihood" })
    ] })
  ] })
);
RiskHeatmap.displayName = "RiskHeatmap";

// packages/ui/src/components/audit/audit-finding.tsx
import * as React80 from "react";
import { jsx as jsx79, jsxs as jsxs74 } from "react/jsx-runtime";
var findingSeverity = cva("inlineFlex itemsCenter rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontBold uppercase", {
  variants: {
    severity: {
      "materialWeakness": "bg-[var(-StatusError)]/20 text-[var(-StatusError)]",
      "significantDeficiency": "bg-[var(-StatusWarning)]/20 text-[var(-StatusWarning)]",
      "deficiency": "bg-[var(-StatusIdle)]/20 text-[var(-TextSecondary)]"
    }
  },
  defaultVariants: { severity: "deficiency" }
});
var AuditFinding = React80.forwardRef(
  ({ className, title, severity, owner, dueDate, description, ...props }, ref) => /* @__PURE__ */ jsxs74("div", { ref, className: cn("flex flexCol gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
    /* @__PURE__ */ jsxs74("div", { className: "flex itemsCenter justifyBetween", children: [
      /* @__PURE__ */ jsx79("span", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: title }),
      /* @__PURE__ */ jsx79("span", { className: findingSeverity({ severity }), children: severity.replace("-", " ") })
    ] }),
    /* @__PURE__ */ jsx79("p", { className: "text-[var(-FontSm)] text-[var(-TextSecondary)]", children: description }),
    /* @__PURE__ */ jsxs74("div", { className: "flex itemsCenter justifyBetween borderT border-[var(-BorderDefault)] pt-[var(-SpacingSm)]", children: [
      /* @__PURE__ */ jsxs74("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: [
        "Owner: ",
        owner
      ] }),
      /* @__PURE__ */ jsxs74("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: [
        "Due: ",
        dueDate
      ] })
    ] })
  ] })
);
AuditFinding.displayName = "AuditFinding";

// packages/ui/src/components/governance/entity-tree.tsx
import * as React81 from "react";
import { jsx as jsx80, jsxs as jsxs75 } from "react/jsx-runtime";
function EntityItem({ node, depth = 0 }) {
  const typeColor2 = { parent: "var(-AccentTeal500)", subsidiary: "var(-ModelGemma)", branch: "var(-ModelQwen)" };
  return /* @__PURE__ */ jsxs75("div", { style: { paddingLeft: `${depth * 20}px` }, children: [
    /* @__PURE__ */ jsxs75("div", { className: "flex itemsCenter gap-[var(-SpacingSm)] py-[var(-SpacingXs)]", children: [
      /* @__PURE__ */ jsx80("span", { className: "h2 w2 roundedFull", style: { backgroundColor: typeColor2[node.type] } }),
      /* @__PURE__ */ jsx80("span", { className: "text-[var(-FontSm)] text-[var(-TextPrimary)]", children: node.name }),
      /* @__PURE__ */ jsxs75("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: [
        "(",
        node.jurisdiction,
        ")"
      ] })
    ] }),
    node.children?.map((child, i) => /* @__PURE__ */ jsx80(EntityItem, { node: child, depth: depth + 1 }, i))
  ] });
}
var EntityTree = React81.forwardRef(
  ({ className, root, ...props }, ref) => /* @__PURE__ */ jsxs75("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
    /* @__PURE__ */ jsx80("div", { className: "mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Corporate Structure" }),
    /* @__PURE__ */ jsx80(EntityItem, { node: root })
  ] })
);
EntityTree.displayName = "EntityTree";

// packages/ui/src/components/governance/disclosure-checklist.tsx
import * as React82 from "react";
import { jsx as jsx81, jsxs as jsxs76 } from "react/jsx-runtime";
var statusIcon = { complete: "\u2713", "inProgress": "\u25CB", "notStarted": "\u2014" };
var statusClass = { complete: "text-[var(-StatusHealthy)]", "inProgress": "text-[var(-StatusWarning)]", "notStarted": "text-[var(-TextMuted)]" };
var DisclosureChecklist = React82.forwardRef(
  ({ className, items, ...props }, ref) => /* @__PURE__ */ jsxs76("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] overflowHidden", className), ...props, children: [
    /* @__PURE__ */ jsx81("div", { className: "borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)]", children: /* @__PURE__ */ jsx81("span", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "SEC Disclosure Checklist" }) }),
    items.map((item, i) => /* @__PURE__ */ jsxs76("div", { className: "flex itemsCenter justifyBetween borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingMd)] last:borderB0 hover:bg-[var(-SurfaceHover)]", children: [
      /* @__PURE__ */ jsxs76("div", { className: "flex itemsCenter gap-[var(-SpacingMd)]", children: [
        /* @__PURE__ */ jsx81("span", { className: cn("fontBold", statusClass[item.status]), children: statusIcon[item.status] }),
        /* @__PURE__ */ jsx81("span", { className: "text-[var(-FontSm)] text-[var(-TextPrimary)]", children: item.requirement })
      ] }),
      /* @__PURE__ */ jsx81("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: item.deadline })
    ] }, i))
  ] })
);
DisclosureChecklist.displayName = "DisclosureChecklist";

// packages/ui/src/components/governance/board-card.tsx
import * as React83 from "react";
import { jsx as jsx82, jsxs as jsxs77 } from "react/jsx-runtime";
var BoardCard = React83.forwardRef(
  ({ className, title, date, attendees, materialsReady, actionItems, ...props }, ref) => /* @__PURE__ */ jsxs77("div", { ref, className: cn("flex flexCol gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
    /* @__PURE__ */ jsxs77("div", { className: "flex itemsCenter justifyBetween", children: [
      /* @__PURE__ */ jsx82("span", { className: "text-[var(-FontMd)] fontSemibold text-[var(-TextPrimary)]", children: title }),
      /* @__PURE__ */ jsx82("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: date })
    ] }),
    /* @__PURE__ */ jsxs77("div", { className: "flex itemsCenter gap-[var(-SpacingLg)] text-[var(-FontXs)]", children: [
      /* @__PURE__ */ jsxs77("span", { className: "text-[var(-TextSecondary)]", children: [
        attendees,
        " attendees"
      ] }),
      /* @__PURE__ */ jsxs77("span", { className: materialsReady ? "text-[var(-StatusHealthy)]" : "text-[var(-StatusWarning)]", children: [
        "Materials: ",
        materialsReady ? "Ready" : "Pending"
      ] }),
      /* @__PURE__ */ jsxs77("span", { className: "text-[var(-TextSecondary)]", children: [
        actionItems,
        " action items"
      ] })
    ] })
  ] })
);
BoardCard.displayName = "BoardCard";

// packages/ui/src/components/governance/ir-metric.tsx
import * as React84 from "react";
import { jsx as jsx83, jsxs as jsxs78 } from "react/jsx-runtime";
var IrMetric = React84.forwardRef(
  ({ className, name, value, target, trend, period, ...props }, ref) => /* @__PURE__ */ jsxs78("div", { ref, className: cn("flex flexCol gap-[var(-SpacingXs)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
    /* @__PURE__ */ jsx83("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)] uppercase trackingWider", children: name }),
    /* @__PURE__ */ jsxs78("div", { className: "flex itemsEnd gap-[var(-SpacingSm)]", children: [
      /* @__PURE__ */ jsx83("span", { className: "fontMono text-[var(-Font2xl)] fontBold text-[var(-TextPrimary)]", children: value }),
      /* @__PURE__ */ jsx83("span", { className: cn("text-[var(-FontSm)] fontMedium", trend === "up" ? "text-[var(-StatusHealthy)]" : trend === "down" ? "text-[var(-StatusError)]" : "text-[var(-TextMuted)]"), children: trend === "up" ? "\u2191" : trend === "down" ? "\u2193" : "\u2192" })
    ] }),
    /* @__PURE__ */ jsxs78("div", { className: "flex itemsCenter justifyBetween", children: [
      target && /* @__PURE__ */ jsxs78("span", { className: "text-[var(-FontXs)] text-[var(-TextSecondary)]", children: [
        "Target: ",
        target
      ] }),
      /* @__PURE__ */ jsx83("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: period })
    ] })
  ] })
);
IrMetric.displayName = "IrMetric";

// packages/ui/src/components/pr/press-card.tsx
import * as React85 from "react";
import { jsx as jsx84, jsxs as jsxs79 } from "react/jsx-runtime";
var PressCard = React85.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs79("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx84("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Press" }),
  /* @__PURE__ */ jsx84("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: label || "Component ready" })
] }));
PressCard.displayName = "PressCard";

// packages/ui/src/components/pr/sentiment-bar.tsx
import * as React86 from "react";
import { jsx as jsx85, jsxs as jsxs80 } from "react/jsx-runtime";
var SentimentBar = React86.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs80("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx85("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Sentiment" }),
  /* @__PURE__ */ jsx85("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: label || "Component ready" })
] }));
SentimentBar.displayName = "SentimentBar";

// packages/ui/src/components/campaigns/campaign-card.tsx
import * as React87 from "react";
import { jsx as jsx86, jsxs as jsxs81 } from "react/jsx-runtime";
var campaignStatus = cva("rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontMedium", {
  variants: { status: { active: "bg-[var(-StatusHealthy)]/15 text-[var(-StatusHealthy)]", draft: "bg-[var(-StatusIdle)]/15 text-[var(-StatusIdle)]", paused: "bg-[var(-StatusWarning)]/15 text-[var(-StatusWarning)]", ended: "bg-[var(-BgTertiary)] text-[var(-TextMuted)]" } },
  defaultVariants: { status: "draft" }
});
var CampaignCard = React87.forwardRef(({ className, name, status, budget, roi, channels, ...props }, ref) => /* @__PURE__ */ jsxs81("div", { ref, className: cn("flex flexCol gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsxs81("div", { className: "flex itemsCenter justifyBetween", children: [
    /* @__PURE__ */ jsx86("span", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: name }),
    /* @__PURE__ */ jsx86("span", { className: campaignStatus({ status }), children: status })
  ] }),
  /* @__PURE__ */ jsxs81("div", { className: "flex itemsCenter gap-[var(-SpacingLg)] text-[var(-FontXs)]", children: [
    /* @__PURE__ */ jsxs81("span", { className: "text-[var(-TextMuted)]", children: [
      "$",
      budget.toLocaleString()
    ] }),
    /* @__PURE__ */ jsxs81("span", { className: cn("fontMono", roi > 0 ? "text-[var(-StatusHealthy)]" : "text-[var(-StatusError)]"), children: [
      roi > 0 ? "+" : "",
      roi,
      "% ROI"
    ] })
  ] }),
  /* @__PURE__ */ jsx86("div", { className: "flex gap-[var(-SpacingXs)]", children: channels.map((ch) => /* @__PURE__ */ jsx86("span", { className: "rounded-[var(-RadiusSm)] bg-[var(-BgTertiary)] px1.5 py0.5 text-[var(-FontXs)] text-[var(-TextMuted)]", children: ch }, ch)) })
] }));
CampaignCard.displayName = "CampaignCard";

// packages/ui/src/components/campaigns/channel-card.tsx
import * as React88 from "react";
import { jsx as jsx87, jsxs as jsxs82 } from "react/jsx-runtime";
var ChannelCard = React88.forwardRef(({ className, channel, visitors, conversions, trend, ...props }, ref) => /* @__PURE__ */ jsxs82("div", { ref, className: cn("flex itemsCenter justifyBetween rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] px-[var(-SpacingLg)] py-[var(-SpacingMd)]", className), ...props, children: [
  /* @__PURE__ */ jsx87("span", { className: "text-[var(-FontSm)] fontMedium text-[var(-TextPrimary)]", children: channel }),
  /* @__PURE__ */ jsxs82("div", { className: "flex itemsCenter gap-[var(-SpacingLg)] text-[var(-FontXs)]", children: [
    /* @__PURE__ */ jsxs82("span", { className: "fontMono text-[var(-TextSecondary)]", children: [
      visitors.toLocaleString(),
      " visits"
    ] }),
    /* @__PURE__ */ jsxs82("span", { className: "fontMono text-[var(-TextSecondary)]", children: [
      conversions,
      " conv"
    ] }),
    /* @__PURE__ */ jsx87("span", { className: cn("fontBold", trend === "up" ? "text-[var(-StatusHealthy)]" : trend === "down" ? "text-[var(-StatusError)]" : "text-[var(-TextMuted)]"), children: trend === "up" ? "\u2191" : trend === "down" ? "\u2193" : "\u2192" })
  ] })
] }));
ChannelCard.displayName = "ChannelCard";

// packages/ui/src/components/campaigns/content-queue.tsx
import * as React89 from "react";
import { jsx as jsx88, jsxs as jsxs83 } from "react/jsx-runtime";
var statusColor2 = { draft: "var(-StatusIdle)", review: "var(-StatusWarning)", scheduled: "var(-AccentTeal500)", published: "var(-StatusHealthy)" };
var ContentQueue = React89.forwardRef(({ className, items, ...props }, ref) => /* @__PURE__ */ jsxs83("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] overflowHidden", className), ...props, children: [
  /* @__PURE__ */ jsx88("div", { className: "borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)]", children: /* @__PURE__ */ jsx88("span", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Content Queue" }) }),
  items.map((item, i) => /* @__PURE__ */ jsxs83("div", { className: "flex itemsCenter gap-[var(-SpacingMd)] borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)] last:borderB0", children: [
    /* @__PURE__ */ jsx88("span", { className: "h2 w2 roundedFull", style: { backgroundColor: statusColor2[item.status] } }),
    /* @__PURE__ */ jsx88("span", { className: "flex1 text-[var(-FontSm)] text-[var(-TextPrimary)]", children: item.title }),
    /* @__PURE__ */ jsx88("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: item.type }),
    /* @__PURE__ */ jsx88("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: item.date })
  ] }, i))
] }));
ContentQueue.displayName = "ContentQueue";

// packages/ui/src/components/incident/postmortem-card.tsx
import * as React90 from "react";
import { jsx as jsx89, jsxs as jsxs84 } from "react/jsx-runtime";
var PostmortemCard = React90.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs84("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx89("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Postmortem Card" }),
  /* @__PURE__ */ jsx89("p", { className: "mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: "Incident postmortem summary" }),
  /* @__PURE__ */ jsx89("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]", children: label || "Ready" })
] }));
PostmortemCard.displayName = "PostmortemCard";

// packages/ui/src/components/incident/oncall-roster.tsx
import * as React91 from "react";
import { jsx as jsx90, jsxs as jsxs85 } from "react/jsx-runtime";
var OncallRoster = React91.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs85("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx90("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "OnCall Roster" }),
  /* @__PURE__ */ jsx90("p", { className: "mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: "Current onCall rotation and schedule" }),
  /* @__PURE__ */ jsx90("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]", children: label || "Ready" })
] }));
OncallRoster.displayName = "OncallRoster";

// packages/ui/src/components/incident/status-page.tsx
import * as React92 from "react";
import { jsx as jsx91, jsxs as jsxs86 } from "react/jsx-runtime";
var StatusPage = React92.forwardRef(({ className, label, ...props }, ref) => /* @__PURE__ */ jsxs86("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx91("div", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "Status Page" }),
  /* @__PURE__ */ jsx91("p", { className: "mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]", children: "Service status indicators" }),
  /* @__PURE__ */ jsx91("div", { className: "mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]", children: label || "Ready" })
] }));
StatusPage.displayName = "StatusPage";

// packages/ui/src/components/raas/tenant-card.tsx
import * as React93 from "react";
import { jsx as jsx92, jsxs as jsxs87 } from "react/jsx-runtime";
var tierBadge = cva("rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontMedium", {
  variants: { tier: { starter: "bg-[var(-StatusIdle)]/15 text-[var(-StatusIdle)]", pro: "bg-[var(-AccentTeal500)]/15 text-[var(-AccentTeal400)]", enterprise: "bg-[var(-Primary)]/15 text-[var(-Primary)]" } },
  defaultVariants: { tier: "starter" }
});
var TenantCard = React93.forwardRef(({ className, name, tier, health, usage, apiCalls, ...props }, ref) => /* @__PURE__ */ jsxs87("div", { ref, className: cn("flex flexCol gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsxs87("div", { className: "flex itemsCenter justifyBetween", children: [
    /* @__PURE__ */ jsx92("span", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: name }),
    /* @__PURE__ */ jsx92("span", { className: tierBadge({ tier }), children: tier })
  ] }),
  /* @__PURE__ */ jsxs87("div", { className: "grid gridCols3 gap-[var(-SpacingSm)] text-[var(-FontXs)]", children: [
    /* @__PURE__ */ jsxs87("div", { className: "flex flexCol", children: [
      /* @__PURE__ */ jsx92("span", { className: "text-[var(-TextMuted)]", children: "Health" }),
      /* @__PURE__ */ jsxs87("span", { className: cn("fontMono", health > 90 ? "text-[var(-StatusHealthy)]" : "text-[var(-StatusWarning)]"), children: [
        health,
        "%"
      ] })
    ] }),
    /* @__PURE__ */ jsxs87("div", { className: "flex flexCol", children: [
      /* @__PURE__ */ jsx92("span", { className: "text-[var(-TextMuted)]", children: "Usage" }),
      /* @__PURE__ */ jsxs87("span", { className: "fontMono text-[var(-TextPrimary)]", children: [
        usage,
        "%"
      ] })
    ] }),
    /* @__PURE__ */ jsxs87("div", { className: "flex flexCol", children: [
      /* @__PURE__ */ jsx92("span", { className: "text-[var(-TextMuted)]", children: "API Calls" }),
      /* @__PURE__ */ jsx92("span", { className: "fontMono text-[var(-TextPrimary)]", children: apiCalls.toLocaleString() })
    ] })
  ] })
] }));
TenantCard.displayName = "TenantCard";

// packages/ui/src/components/raas/sdk-preview.tsx
import * as React94 from "react";
import { jsx as jsx93, jsxs as jsxs88 } from "react/jsx-runtime";
var SdkPreview = React94.forwardRef(({ className, language, code, endpoint, ...props }, ref) => /* @__PURE__ */ jsxs88("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] overflowHidden", className), ...props, children: [
  /* @__PURE__ */ jsxs88("div", { className: "flex itemsCenter justifyBetween borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)]", children: [
    /* @__PURE__ */ jsx93("span", { className: "text-[var(-FontXs)] fontSemibold text-[var(-TextPrimary)] uppercase", children: language }),
    /* @__PURE__ */ jsx93("span", { className: "fontMono text-[var(-FontXs)] text-[var(-TextMuted)]", children: endpoint })
  ] }),
  /* @__PURE__ */ jsx93("pre", { className: "p-[var(-SpacingLg)] fontMono text-[var(-FontXs)] text-[var(-AccentTeal400)] overflowXAuto", children: code })
] }));
SdkPreview.displayName = "SdkPreview";

// packages/ui/src/components/raas/gateway-status.tsx
import * as React95 from "react";
import { jsx as jsx94, jsxs as jsxs89 } from "react/jsx-runtime";
var GatewayStatus = React95.forwardRef(({ className, routes, latencyMs, uptime, ...props }, ref) => /* @__PURE__ */ jsxs89("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
  /* @__PURE__ */ jsx94("div", { className: "mb-[var(-SpacingSm)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "API Gateway" }),
  /* @__PURE__ */ jsxs89("div", { className: "grid gridCols3 gap-[var(-SpacingMd)]", children: [
    /* @__PURE__ */ jsxs89("div", { className: "flex flexCol", children: [
      /* @__PURE__ */ jsx94("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: "Routes" }),
      /* @__PURE__ */ jsx94("span", { className: "fontMono text-[var(-FontLg)] text-[var(-TextPrimary)]", children: routes })
    ] }),
    /* @__PURE__ */ jsxs89("div", { className: "flex flexCol", children: [
      /* @__PURE__ */ jsx94("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: "P50 Latency" }),
      /* @__PURE__ */ jsxs89("span", { className: "fontMono text-[var(-FontLg)] text-[var(-TextPrimary)]", children: [
        latencyMs,
        "ms"
      ] })
    ] }),
    /* @__PURE__ */ jsxs89("div", { className: "flex flexCol", children: [
      /* @__PURE__ */ jsx94("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: "Uptime" }),
      /* @__PURE__ */ jsxs89("span", { className: cn("fontMono text-[var(-FontLg)]", uptime > 99.9 ? "text-[var(-StatusHealthy)]" : "text-[var(-StatusWarning)]"), children: [
        uptime,
        "%"
      ] })
    ] })
  ] })
] }));
GatewayStatus.displayName = "GatewayStatus";

// packages/ui/src/components/raas/mcu-gauge.tsx
import * as React96 from "react";
import { jsx as jsx95, jsxs as jsxs90 } from "react/jsx-runtime";
var McuGauge = React96.forwardRef(({ className, used, total, tier, ...props }, ref) => {
  const pct = Math.round(used / total * 100);
  return /* @__PURE__ */ jsxs90("div", { ref, className: cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className), ...props, children: [
    /* @__PURE__ */ jsxs90("div", { className: "flex itemsCenter justifyBetween mb-[var(-SpacingSm)]", children: [
      /* @__PURE__ */ jsx95("span", { className: "text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]", children: "MCU Credits" }),
      /* @__PURE__ */ jsx95("span", { className: "text-[var(-FontXs)] text-[var(-TextMuted)]", children: tier })
    ] }),
    /* @__PURE__ */ jsxs90("div", { className: "fontMono text-[var(-Font2xl)] fontBold text-[var(-TextPrimary)]", children: [
      used,
      /* @__PURE__ */ jsxs90("span", { className: "text-[var(-FontSm)] text-[var(-TextMuted)]", children: [
        "/",
        total
      ] })
    ] }),
    /* @__PURE__ */ jsx95("div", { className: "mt-[var(-SpacingSm)] h2 wFull roundedFull bg-[var(-BgTertiary)] overflowHidden", children: /* @__PURE__ */ jsx95("div", { className: cn("hFull roundedFull transitionAll", pct > 90 ? "bg-[var(-StatusError)]" : pct > 70 ? "bg-[var(-StatusWarning)]" : "bg-[var(-AccentTeal500)]"), style: { width: `${pct}%` } }) })
  ] });
});
McuGauge.displayName = "McuGauge";
export {
  AccessMatrix,
  ActivityFeed,
  AgentAvatar,
  AlertRule,
  AttributionChart,
  AuditFinding,
  Badge,
  BoardCard,
  BotStatus,
  BudgetBar,
  Button,
  CampaignCard,
  CandidateCard,
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  ChannelCard,
  ChurnRisk,
  CodeBlock,
  CommandPalette,
  ComplianceGauge,
  ComplianceStatus,
  ContentQueue,
  ContractCard,
  ControlCard,
  CostTracker,
  CreditGauge,
  CreditMeter,
  Customer360,
  DealCard,
  DeltaPattern,
  DisclosureChecklist,
  EntityTree,
  EvalSuite,
  ExperimentCard,
  FeatureBento,
  FeatureFlag,
  FilingStatus,
  ForecastChart,
  GatewayStatus,
  GuardrailLog,
  HealthScore,
  HeroSection,
  IncidentTimeline,
  Input,
  IrMetric,
  JourneyMap,
  Kbd,
  KpiCard,
  LineageGraph,
  LoadingRiver,
  LogViewer,
  McuGauge,
  MekongLogo,
  MekongMotif,
  MekongWordmark,
  MetricCard,
  MetricDefinition,
  MilestoneTrack,
  MissionCard,
  ModelCard,
  NpsGauge,
  OncallRoster,
  OrderBook,
  OrgNode,
  PerfGauge,
  PipelineBadge,
  PipelineDag,
  PipelineFunnel,
  PipelineStage,
  PipelineViz,
  PolicyStatus,
  PositionCard,
  PostmortemCard,
  PressCard,
  PriceDisplay,
  PricingTable,
  ProbabilityChart,
  QualityScore,
  ReadinessScore,
  RevenueChart,
  RiskHeatmap,
  RoadmapLane,
  SdkPreview,
  SegmentBuilder,
  SentimentBar,
  Skeleton,
  SlaTracker,
  SoxProgress,
  StatusDot,
  StatusPage,
  TenantCard,
  TerminalDemo,
  ThreatFeed,
  TicketCard,
  TraceWaterfall,
  TrustBar,
  VulnCard,
  badgeVariants,
  buttonVariants,
  cardVariants,
  findingSeverity,
  pipelineBadgeVariants,
  policyStatusVariants,
  statusDotVariants,
  testStatusVariants,
  vulnSeverityVariants
};
