import type { StateCreator, StoreApi, StoreMutatorIdentifier } from 'zustand/vanilla';
type Config = Parameters<(Window extends {
    __REDUX_DEVTOOLS_EXTENSION__?: infer T;
} ? T : {
    connect: (param: any) => unknown;
})['connect']>[0];
declare module '../vanilla' {
    interface StoreMutators<S, A> {
        'zustand/devtools': WithDevtools<S>;
    }
}
type Cast<T, U> = T extends U ? T : U;
type Write<T, U> = Omit<T, keyof U> & U;
type TakeTwo<T> = T extends {
    length: 0;
} ? [undefined, undefined] : T extends {
    length: 1;
} ? [...args0: Cast<T, unknown[]>, arg1: undefined] : T extends {
    length: 0 | 1;
} ? [...args0: Cast<T, unknown[]>, arg1: undefined] : T extends {
    length: 2;
} ? T : T extends {
    length: 1 | 2;
} ? T : T extends {
    length: 0 | 1 | 2;
} ? T : T extends [infer A0, infer A1, ...unknown[]] ? [A0, A1] : T extends [infer A0, (infer A1)?, ...unknown[]] ? [A0, A1?] : T extends [(infer A0)?, (infer A1)?, ...unknown[]] ? [A0?, A1?] : never;
type WithDevtools<S> = Write<S, StoreDevtools<S>>;
type Action = string | {
    type: string;
    [x: string | number | symbol]: unknown;
};
type StoreDevtools<S> = S extends {
    setState: {
        (...args: infer Sa1): infer Sr1;
        (...args: infer Sa2): infer Sr2;
    };
} ? {
    setState(...args: [...args: TakeTwo<Sa1>, action?: Action]): Sr1;
    setState(...args: [...args: TakeTwo<Sa2>, action?: Action]): Sr2;
    devtools: {
        cleanup: () => void;
    };
} : never;
type Join<Prefix extends string, K extends string> = Prefix extends '' ? K : `${Prefix}${K}`;
type NextPrefix<Prefix extends string, K extends string> = Prefix extends '' ? `${K}.` : `${Prefix}${K}.`;
type FunctionPaths<T, Prefix extends string = ''> = {
    [K in keyof T & string]: T[K] extends (...args: any[]) => any ? Join<Prefix, K> : T[K] extends Record<string, any> ? FunctionPaths<T[K], NextPrefix<Prefix, K>> extends infer P ? P extends string ? P | `${Prefix}${K}.*` | `${Prefix}${K}.**` : never : never : never;
}[keyof T & string];
type ActionCreators<T extends Record<string, any>> = {
    [K in FunctionPaths<T> | '*' | '**' | (string & {})]?: boolean | (K extends '*' | '**' | `${string}.*` | `${string}.**` ? never : (...args: any[]) => void);
};
export interface DevtoolsOptions<T extends Record<string, unknown> = Record<string, unknown>> extends Omit<Config, 'actionCreators'> {
    name?: string;
    enabled?: boolean;
    anonymousActionType?: string;
    store?: string;
    actionCreators?: ActionCreators<T>;
}
type Devtools = <T, Mps extends [StoreMutatorIdentifier, unknown][] = [], Mcs extends [StoreMutatorIdentifier, unknown][] = [], U = T>(initializer: StateCreator<T, [...Mps, ['zustand/devtools', never]], Mcs, U>, devtoolsOptions?: DevtoolsOptions<T & {}>) => StateCreator<T, Mps, [['zustand/devtools', never], ...Mcs], U>;
export type NamedSet<T> = WithDevtools<StoreApi<T>>['setState'];
export declare const devtools: Devtools;
export {};
