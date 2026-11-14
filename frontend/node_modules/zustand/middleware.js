'use strict';

const reduxImpl = (reducer, initial) => (set, _get, api) => {
  api.dispatch = (action) => {
    set((state) => reducer(state, action), false, action);
    return action;
  };
  api.dispatchFromDevtools = true;
  return { dispatch: (...args) => api.dispatch(...args), ...initial };
};
const redux = reduxImpl;

const shouldDispatchFromDevtools = (api) => !!api.dispatchFromDevtools && typeof api.dispatch === "function";
const trackedConnections = /* @__PURE__ */ new Map();
const getTrackedConnectionState = (name) => {
  const api = trackedConnections.get(name);
  if (!api) return {};
  return Object.fromEntries(
    Object.entries(api.stores).map(([key, api2]) => [key, api2.getState()])
  );
};
const extractConnectionInformation = (store, extensionConnector, options) => {
  if (store === void 0) {
    return {
      type: "untracked",
      connection: extensionConnector.connect(options)
    };
  }
  const existingConnection = trackedConnections.get(options.name);
  if (existingConnection) {
    return { type: "tracked", store, ...existingConnection };
  }
  const newConnection = {
    connection: extensionConnector.connect(options),
    stores: {}
  };
  trackedConnections.set(options.name, newConnection);
  return { type: "tracked", store, ...newConnection };
};
const removeStoreFromTrackedConnections = (name, store, api) => {
  if (store === void 0) return;
  const connectionInfo = trackedConnections.get(name);
  if ((connectionInfo == null ? void 0 : connectionInfo.stores[store]) !== api) return;
  delete connectionInfo.stores[store];
  if (Object.keys(connectionInfo.stores).length === 0) {
    trackedConnections.delete(name);
  }
};
const v8StackLineRe = /^at (?:new |async )?(.+?) \(/;
const geckoStackLineRe = /^([^@]+)@/;
function findCallerName(stack) {
  var _a, _b, _c;
  if (!stack) return void 0;
  const traceLines = stack.split("\n");
  const apiSetStateLineIndex = traceLines.findIndex(
    (traceLine) => traceLine.includes("api.setState")
  );
  if (apiSetStateLineIndex < 0) return void 0;
  const callerLine = ((_a = traceLines[apiSetStateLineIndex + 1]) == null ? void 0 : _a.trim()) || "";
  return ((_b = v8StackLineRe.exec(callerLine)) == null ? void 0 : _b[1]) || ((_c = geckoStackLineRe.exec(callerLine)) == null ? void 0 : _c[1]);
}
const devtoolsImpl = (fn, devtoolsOptions = {}) => (set, get, api) => {
  const { enabled, anonymousActionType, store, actionCreators, ...options } = devtoolsOptions;
  let extensionConnector;
  try {
    extensionConnector = (enabled != null ? enabled : process.env.NODE_ENV !== "production") && window.__REDUX_DEVTOOLS_EXTENSION__;
  } catch (e) {
  }
  if (!extensionConnector) {
    return fn(set, get, api);
  }
  let connection = void 0;
  let isRecording = true;
  api.setState = ((state, replace, nameOrAction) => {
    const r = set(state, replace);
    if (!isRecording) return r;
    const action = nameOrAction === void 0 ? {
      type: anonymousActionType || findCallerName(new Error().stack) || "anonymous"
    } : typeof nameOrAction === "string" ? { type: nameOrAction } : nameOrAction;
    if (store === void 0) {
      connection == null ? void 0 : connection.send(action, get());
      return r;
    }
    connection == null ? void 0 : connection.send(
      {
        ...action,
        type: `${store}/${action.type}`
      },
      {
        ...getTrackedConnectionState(options.name),
        [store]: api.getState()
      }
    );
    return r;
  });
  let unsubscribeFromStore;
  api.devtools = {
    cleanup: () => {
      unsubscribeFromStore == null ? void 0 : unsubscribeFromStore();
      unsubscribeFromStore = void 0;
      removeStoreFromTrackedConnections(options.name, store, api);
      if ((store === void 0 || !trackedConnections.has(options.name)) && connection && typeof connection.unsubscribe === "function") {
        connection.unsubscribe();
      }
    }
  };
  const setStateFromDevtools = (...a) => {
    const originalIsRecording = isRecording;
    isRecording = false;
    set(...a);
    isRecording = originalIsRecording;
  };
  const initialState = fn(api.setState, get, api);
  const actionCreatorObjects = actionCreators && getActionCreatorObjects(initialState, actionCreators);
  const connectionInformation = extractConnectionInformation(
    store,
    extensionConnector,
    { ...options, actionCreators: actionCreatorObjects }
  );
  connection = connectionInformation.connection;
  const findActionCreator = (name) => {
    const actionCreator = actionCreatorObjects == null ? void 0 : actionCreatorObjects.find(
      (candidate) => candidate.name === name
    );
    if (!actionCreator && actionCreators && store === void 0) {
      console.error(
        `[zustand devtools middleware] Action type "${name}" not found in actionCreators`
      );
    }
    return actionCreator;
  };
  if (connectionInformation.type === "untracked") {
    connection == null ? void 0 : connection.init(initialState);
  } else {
    connectionInformation.stores[connectionInformation.store] = api;
    connection == null ? void 0 : connection.init(
      Object.fromEntries(
        Object.entries(connectionInformation.stores).map(([key, store2]) => [
          key,
          key === connectionInformation.store ? initialState : store2.getState()
        ])
      )
    );
  }
  if (shouldDispatchFromDevtools(api)) {
    let didWarnAboutReservedActionType = false;
    const originalDispatch = api.dispatch;
    api.dispatch = (...args) => {
      if (process.env.NODE_ENV !== "production" && args[0].type === "__setState" && !didWarnAboutReservedActionType) {
        console.warn(
          '[zustand devtools middleware] "__setState" action type is reserved to set state from the devtools. Avoid using it.'
        );
        didWarnAboutReservedActionType = true;
      }
      originalDispatch(...args);
    };
  }
  unsubscribeFromStore = connection.subscribe((message) => {
    var _a;
    const reviver = typeof options.serialize === "object" ? options.serialize.reviver : void 0;
    switch (message.type) {
      case "ACTION": {
        if (typeof message.payload !== "string") {
          if (shouldDispatchFromDevtools(api)) {
            console.error(
              '[zustand devtools middleware] The action dropdown is not supported with the redux middleware. Dispatch a custom action in JSON format instead, e.g. { "type": "increment" }'
            );
            return;
          }
          if (!actionCreators) {
            console.error(
              "[zustand devtools middleware] Unsupported action format"
            );
            return;
          }
          const actionCreator2 = findActionCreator(message.payload.name);
          if (!actionCreator2) return;
          const args2 = parseDropdownArgs(message.payload, reviver);
          if (!args2) return;
          return actionCreator2.func(...args2);
        }
        let action;
        try {
          action = JSON.parse(message.payload, reviver);
        } catch (e) {
          let errorMessage = `[zustand devtools middleware] Malformed JSON. When dispatching custom actions, please format the payload as a JSON string.
              Examples:`;
          if (shouldDispatchFromDevtools(api)) {
            errorMessage += `
              - { "type": "increment", "amount": 1 }
              - { "type": "reset" }
              `;
          } else {
            errorMessage += `
              - { "type": "increment" }
              - { "type": "increment", "args": [1] }
              If you have args with default values or want to be \`undefined\`, prefer using the object syntax so you can omit them.
              - { "type": "increment", "args": { "amount": 1 } }
              `;
          }
          console.error(errorMessage.replace(/\n\s+/g, "\n"));
          return;
        }
        if (action.type === "__setState") {
          if (store === void 0) {
            if (!("state" in action)) {
              console.warn(
                `
                  [zustand devtools middleware] Calling __setState without a state property.
                  This may not be what you intended, you should explicitly set the state you want to set.
                  Example: { "type": "__setState", "state": { "foo": "bar" } }
                  `.replace(/\n\s+/g, "\n")
              );
              return;
            }
            setStateFromDevtools(action.state);
            return;
          }
          if (Object.keys(action.state).length !== 1) {
            console.error(
              `
                [zustand devtools middleware] Unsupported __setState action format.
                When using 'store' option in devtools(), the 'state' should have only one key, which is a value of 'store' that was passed in devtools(),
                and value of this only key should be a state object. Example: { "type": "__setState", "state": { "abc123Store": { "foo": "bar" } } }
                `.replace(/\n\s+/g, "\n")
            );
          }
          const stateFromDevtools = action.state[store];
          if (stateFromDevtools === void 0 || stateFromDevtools === null) {
            return;
          }
          if (JSON.stringify(api.getState()) !== JSON.stringify(stateFromDevtools)) {
            setStateFromDevtools(stateFromDevtools);
          }
          return;
        }
        if (shouldDispatchFromDevtools(api)) {
          api.dispatch(action);
          return;
        }
        const actionCreator = findActionCreator(action.type);
        if (!actionCreator) return;
        const args = action.args;
        return actionCreator.func(
          ...Array.isArray(args) ? args : actionCreator.args.map((name) => args == null ? void 0 : args[name])
        );
      }
      case "DISPATCH":
        switch (message.payload.type) {
          case "RESET":
            setStateFromDevtools(initialState);
            if (store === void 0) {
              return connection == null ? void 0 : connection.init(api.getState());
            }
            return connection == null ? void 0 : connection.init(getTrackedConnectionState(options.name));
          case "COMMIT":
            if (store === void 0) {
              connection == null ? void 0 : connection.init(api.getState());
              return;
            }
            return connection == null ? void 0 : connection.init(getTrackedConnectionState(options.name));
          case "ROLLBACK":
            return parseJsonThen(message.state, reviver, (state) => {
              if (store === void 0) {
                setStateFromDevtools(state);
                connection == null ? void 0 : connection.init(api.getState());
                return;
              }
              setStateFromDevtools(state[store]);
              connection == null ? void 0 : connection.init(getTrackedConnectionState(options.name));
            });
          case "JUMP_TO_STATE":
          case "JUMP_TO_ACTION":
            return parseJsonThen(message.state, reviver, (state) => {
              if (store === void 0) {
                setStateFromDevtools(state);
                return;
              }
              if (JSON.stringify(api.getState()) !== JSON.stringify(state[store])) {
                setStateFromDevtools(state[store]);
              }
            });
          case "IMPORT_STATE": {
            const { nextLiftedState } = message.payload;
            const lastComputedState = (_a = nextLiftedState.computedStates.slice(-1)[0]) == null ? void 0 : _a.state;
            if (!lastComputedState) return;
            if (store === void 0) {
              setStateFromDevtools(lastComputedState);
            } else {
              setStateFromDevtools(lastComputedState[store]);
            }
            connection == null ? void 0 : connection.send(
              null,
              // FIXME no-any
              nextLiftedState
            );
            return;
          }
          case "PAUSE_RECORDING":
            return isRecording = !isRecording;
        }
        return;
    }
  });
  return initialState;
};
const devtools = devtoolsImpl;
const parseJsonThen = (stringified, reviver, fn) => {
  let parsed;
  try {
    parsed = JSON.parse(stringified, reviver);
  } catch (e) {
    console.error(
      "[zustand devtools middleware] Could not parse the received json",
      e
    );
  }
  if (parsed !== void 0) fn(parsed);
};
function maskToRegex(mask) {
  const escaped = mask.replace(/[.+?^${}()|[\]\\]/g, "\\$&").replace(/\*\*|\*/g, (wildcard) => wildcard === "**" ? ".*" : "[^.]*");
  return new RegExp(`^${escaped}$`);
}
const isPlainObject = (value) => typeof value === "object" && value !== null && Object.getPrototypeOf(value) === Object.prototype;
const getStateFunctions = (state, walked = /* @__PURE__ */ new Map()) => {
  var _a;
  if (!isPlainObject(state)) return [];
  const known = walked.get(state);
  if (known) return known;
  walked.set(state, []);
  const functions = [];
  for (const key of Object.keys(state)) {
    const value = (_a = Object.getOwnPropertyDescriptor(state, key)) == null ? void 0 : _a.value;
    if (typeof value === "function") {
      functions.push([key, value]);
    } else {
      for (const [path, func] of getStateFunctions(value, walked)) {
        functions.push([`${key}.${path}`, func]);
      }
    }
  }
  walked.set(state, functions);
  return functions;
};
const sourceTokenRe = /"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`|\/\*[\s\S]*?\*\/|\/\/.*|[\s\S]/g;
const getParamNames = (func) => {
  var _a, _b;
  const tokens = ((_a = func.toString().match(sourceTokenRe)) != null ? _a : []).filter(
    (token) => !/^\/[/*]/.test(token)
  );
  const arrowParam = (_b = /^(?:async\s+)?([^\s(=]+)\s*=>/.exec(tokens.join(""))) == null ? void 0 : _b[1];
  if (arrowParam) return [arrowParam];
  const params = [""];
  let depth = 0;
  let inDefaultValue = false;
  for (const token of tokens.slice(tokens.indexOf("(") + 1)) {
    if (depth === 0) {
      if (token === ")") break;
      if (token === ",") {
        params.push("");
        inDefaultValue = false;
        continue;
      }
      if (token === "=") inDefaultValue = true;
    }
    if ("([{".includes(token)) depth++;
    if (")]}".includes(token)) depth--;
    if (!inDefaultValue) params[params.length - 1] += token;
  }
  return params.map((param) => param.trim()).filter((param) => param && !param.startsWith("..."));
};
const createActionCreatorObject = (name, func) => ({ name, func, args: getParamNames(func) });
function getActionCreatorObjects(state, actionCreators) {
  const actions = /* @__PURE__ */ new Map();
  const matchers = Object.entries(actionCreators).map(([key, picked]) => ({
    matcher: maskToRegex(key),
    picked,
    key
  })).sort((a, b) => {
    const aIsDoubleWildcard = a.key.includes("**");
    const bIsDoubleWildcard = b.key.includes("**");
    if (aIsDoubleWildcard !== bIsDoubleWildcard) {
      return aIsDoubleWildcard ? -1 : 1;
    }
    const aIsSingleWildcard = a.key.includes("*") && !aIsDoubleWildcard;
    const bIsSingleWildcard = b.key.includes("*") && !bIsDoubleWildcard;
    if (aIsSingleWildcard !== bIsSingleWildcard) {
      return aIsSingleWildcard ? -1 : 1;
    }
    return a.key.length - b.key.length;
  });
  for (const [name, func] of getStateFunctions(state)) {
    for (const { matcher, picked } of matchers) {
      if (matcher.test(name)) {
        if (picked === false) {
          actions.delete(name);
          continue;
        }
        actions.set(name, createActionCreatorObject(name, func));
      }
    }
  }
  for (const [name, picked] of Object.entries(actionCreators)) {
    if (typeof picked === "function") {
      actions.set(name, createActionCreatorObject(name, picked));
    }
  }
  return Array.from(actions.values());
}
const parseDropdownArgs = ({ args, rest }, reviver) => {
  var _a;
  const parse = (arg) => arg ? JSON.parse(arg, reviver) : void 0;
  try {
    const restArgs = (_a = parse(rest)) != null ? _a : [];
    if (!Array.isArray(restArgs)) throw new Error("...rest is not an array");
    return [...args.map(parse), ...restArgs];
  } catch (e) {
    console.error(
      '[zustand devtools middleware] Could not parse the arguments from the action dropdown. Each one must be JSON, e.g. 5, "foo" or { "by": 5 }, and ...rest a JSON array.',
      e
    );
    return void 0;
  }
};

const subscribeWithSelectorImpl = (fn) => (set, get, api) => {
  const origSubscribe = api.subscribe;
  api.subscribe = ((selector, optListener, options) => {
    let listener = selector;
    if (optListener) {
      const equalityFn = (options == null ? void 0 : options.equalityFn) || Object.is;
      let currentSlice = selector(api.getState());
      listener = (state) => {
        const nextSlice = selector(state);
        if (!equalityFn(currentSlice, nextSlice)) {
          const previousSlice = currentSlice;
          optListener(currentSlice = nextSlice, previousSlice);
        }
      };
      if (options == null ? void 0 : options.fireImmediately) {
        optListener(currentSlice, currentSlice);
      }
    }
    return origSubscribe(listener);
  });
  const initialState = fn(set, get, api);
  return initialState;
};
const subscribeWithSelector = subscribeWithSelectorImpl;

function combine(initialState, create) {
  return (...args) => Object.assign({}, initialState, create(...args));
}

function createJSONStorage(getStorage, options) {
  let storage;
  try {
    storage = getStorage();
  } catch (e) {
    return;
  }
  const persistStorage = {
    getItem: (name) => {
      var _a;
      const parse = (str2) => {
        if (str2 === null) {
          return null;
        }
        return JSON.parse(str2, options == null ? void 0 : options.reviver);
      };
      const str = (_a = storage.getItem(name)) != null ? _a : null;
      if (isPromiseLike(str)) {
        return str.then(parse);
      }
      return parse(str);
    },
    setItem: (name, newValue) => storage.setItem(name, JSON.stringify(newValue, options == null ? void 0 : options.replacer)),
    removeItem: (name) => storage.removeItem(name)
  };
  return persistStorage;
}
const isPromiseLike = (value) => typeof (value == null ? void 0 : value.then) === "function";
const toSyncThenable = (value) => ({
  then(onFulfilled) {
    return onFulfilled ? toThenable(onFulfilled)(value) : this;
  }
});
const toThenable = (fn) => (input) => {
  try {
    const result = fn(input);
    return isPromiseLike(result) ? result : toSyncThenable(result);
  } catch (error) {
    return {
      then(_onFulfilled, onRejected) {
        return onRejected ? toThenable(onRejected)(error) : this;
      }
    };
  }
};
const persistImpl = (config, baseOptions) => (set, get, api) => {
  let options = {
    storage: createJSONStorage(() => window.localStorage),
    partialize: (state) => state,
    version: 0,
    merge: (persistedState, currentState) => ({
      ...currentState,
      ...persistedState
    }),
    ...baseOptions
  };
  let hasHydrated = false;
  let hydrationVersion = 0;
  const hydrationListeners = /* @__PURE__ */ new Set();
  const finishHydrationListeners = /* @__PURE__ */ new Set();
  let storage = options.storage;
  if (!storage) {
    return config(
      (...args) => {
        console.warn(
          `[zustand persist middleware] Unable to update item '${options.name}', the given storage is currently unavailable.`
        );
        set(...args);
      },
      get,
      api
    );
  }
  const setItem = () => {
    const state = options.partialize({ ...get() });
    return storage.setItem(options.name, {
      state,
      version: options.version
    });
  };
  const savedSetState = api.setState;
  api.setState = (...args) => {
    savedSetState(...args);
    return setItem();
  };
  const configResult = config(
    (...args) => {
      set(...args);
      return setItem();
    },
    get,
    api
  );
  api.getInitialState = () => configResult;
  let stateFromStorage;
  const hydrate = () => {
    var _a, _b;
    if (!storage) return;
    const currentVersion = ++hydrationVersion;
    hasHydrated = false;
    hydrationListeners.forEach((cb) => {
      var _a2;
      return cb((_a2 = get()) != null ? _a2 : configResult);
    });
    const postRehydrationCallback = ((_b = options.onRehydrateStorage) == null ? void 0 : _b.call(options, (_a = get()) != null ? _a : configResult)) || void 0;
    return toThenable(storage.getItem.bind(storage))(options.name).then((deserializedStorageValue) => {
      if (deserializedStorageValue) {
        if (typeof deserializedStorageValue.version === "number" && deserializedStorageValue.version !== options.version) {
          if (options.migrate) {
            const migration = options.migrate(
              deserializedStorageValue.state,
              deserializedStorageValue.version
            );
            if (isPromiseLike(migration)) {
              return migration.then((result) => [true, result]);
            }
            return [true, migration];
          }
          console.error(
            `State loaded from storage couldn't be migrated since no migrate function was provided`
          );
        } else {
          return [false, deserializedStorageValue.state];
        }
      }
      return [false, void 0];
    }).then((migrationResult) => {
      var _a2;
      if (currentVersion !== hydrationVersion) {
        return;
      }
      const [migrated, migratedState] = migrationResult;
      stateFromStorage = options.merge(
        migratedState,
        (_a2 = get()) != null ? _a2 : configResult
      );
      set(stateFromStorage, true);
      if (migrated) {
        return setItem();
      }
    }).then(() => {
      if (currentVersion !== hydrationVersion) {
        return;
      }
      postRehydrationCallback == null ? void 0 : postRehydrationCallback(get(), void 0);
      stateFromStorage = get();
      hasHydrated = true;
      finishHydrationListeners.forEach((cb) => cb(stateFromStorage));
    }).then(
      () => void 0,
      (e) => {
        if (currentVersion !== hydrationVersion) {
          return;
        }
        postRehydrationCallback == null ? void 0 : postRehydrationCallback(void 0, e);
      }
    );
  };
  api.persist = {
    setOptions: (newOptions) => {
      options = {
        ...options,
        ...newOptions
      };
      if (newOptions.storage) {
        storage = newOptions.storage;
      }
    },
    clearStorage: () => {
      ++hydrationVersion;
      storage == null ? void 0 : storage.removeItem(options.name);
    },
    getOptions: () => options,
    rehydrate: () => {
      try {
        return Promise.resolve(hydrate());
      } catch (error) {
        return Promise.reject(error);
      }
    },
    hasHydrated: () => hasHydrated,
    onHydrate: (cb) => {
      hydrationListeners.add(cb);
      return () => {
        hydrationListeners.delete(cb);
      };
    },
    onFinishHydration: (cb) => {
      finishHydrationListeners.add(cb);
      return () => {
        finishHydrationListeners.delete(cb);
      };
    }
  };
  if (!options.skipHydration) {
    hydrate();
  }
  return stateFromStorage || configResult;
};
const persist = persistImpl;

function ssrSafe(config, isSSR = typeof window === "undefined") {
  return (set, get, api) => {
    if (!isSSR) {
      return config(set, get, api);
    }
    const ssrSet = () => {
      throw new Error("Cannot set state of Zustand store in SSR");
    };
    api.setState = ssrSet;
    return config(ssrSet, get, api);
  };
}

exports.combine = combine;
exports.createJSONStorage = createJSONStorage;
exports.devtools = devtools;
exports.persist = persist;
exports.redux = redux;
exports.subscribeWithSelector = subscribeWithSelector;
exports.unstable_ssrSafe = ssrSafe;
