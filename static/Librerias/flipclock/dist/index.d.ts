import { Signal } from 'solid-js';
import { Duration } from 'date-fns';
export { add, sub } from 'date-fns';
import { Properties } from 'csstype';

/**
 * The event instance.
 *
 * @public
 */
type Event<T, K extends keyof T> = {
    key: keyof T;
    fn: EventEmitterCallback<T, K>;
    unwatch: () => void;
};
/**
 * The callback from the event emitter.
 *
 * @public
 */
type EventEmitterCallback<T, K extends keyof Required<T>> = (...args: Required<T>[K][]) => void;
/**
 * An event emitter to facilitate emitter and listening for events.
 *
 * @public
 */
declare class EventEmitter<T> {
    /**
     * The registered events.
     *
     * @protected
     */
    protected events: Event<T, any>[];
    /**
     * Emit an event.
     *
     * @public
    */
    emit<K extends keyof Required<T>>(key: K, ...args: Required<T>[K] extends (...args: infer P) => void ? P : any[]): void;
    /**
     * Listen for an event. This returns a function to unwatch the event.
     *
     * @public
     */
    on<K extends keyof Required<T>>(key: K, fn: EventEmitterCallback<T, K>): () => void;
    /**
     * Listen for an event once.
     *
     * @public
     */
    once<K extends keyof Required<T>>(key: K, fn: EventEmitterCallback<T, K>): () => void;
    /**
     * Stop listening for all events using a, or with a key and a function.
     *
     * @public
     */
    off<K extends keyof Required<T>>(key: K): void;
    off<K extends keyof Required<T>>(key: K, fn: T[K]): void;
    /**
     * Reset the event bus and remove all watchers.
     *
     * @public
     */
    reset(): void;
}
declare function eventEmitter<T>(): EventEmitter<T>;

/**
 * A single digitized value.
 *
 * @public
 */
type DigitizedValue = string;
/**
 * An array of digitized values.
 *
 * @public
 */
type DigitizedValues = (DigitizedValue | DigitizedValues)[];
/**
 * The default empty character for digitization.
 *
 * @public
 */
declare const EMPTY_CHAR = " ";
/**
 * The return type for `useDigitizer()`.
 *
 * @public
 */
type UseDigitizer = {
    digitize: (value: any) => DigitizedValues;
    isDigitized: (value: any) => boolean;
};
/**
 * Create a digiter that can be used to convert a string into arrays of
 * individual characters.
 *
 * @public
 */
declare function useDigitizer(): UseDigitizer;

/**
 * The `FaceValue` face options.
 *
 * @public
 */
type FaceValueProps = {
    /**
     * The digitized values.
     */
    digits?: DigitizedValues;
    /**
     * The digitizer instance.
     */
    digitizer?: UseDigitizer;
};
/**
 * The FaceValue class digitizes the raw value and so it can be used by the
 * clock face.
 *
 * @public
 */
declare class FaceValue<T extends Exclude<unknown, Function>> {
    /**
     * Parameters that are passed to the digiter.
     *
     * @public
     */
    readonly digitizer: UseDigitizer;
    /**
     * The face's value.
     *
     * @protected
     */
    protected $value: Signal<T>;
    /**
     * The face's digits.
     *
     * @protected
     */
    protected $digits: Signal<DigitizedValues>;
    /**
     * Instantiate the face value.
     *
     * @public
     */
    constructor(value: T, props?: FaceValueProps);
    /**
     * The digitized value.
     *
     * @public
     */
    get digits(): DigitizedValues;
    /**
     * Set the digits from a `DigitizedValues`.
     *
     * @public
     */
    set digits(value: DigitizedValues);
    /**
     * Get the length of the flattened digitized array.
     *
     * @public
     */
    get length(): number;
    /**
     * Get the value.
     *
     * @public
     */
    get value(): T;
    /**
     * Set the value.
     *
     * @public
     */
    set value(value: Exclude<T, Function>);
    /**
     * Compare the face value with the given subject.
     *
     * @public
     */
    compare(subject?: FaceValue<any>): boolean;
    /**
     * Create a new instance with the given value.
     *
     * @public
     */
    copy(): FaceValue<T>;
}
/**
 * Create a new `FaceValue` instance.
 *
 * @public
 */
declare function faceValue<T>(value: T): FaceValue<T>;
declare function faceValue<T>(value: T, props: FaceValueProps): FaceValue<T>;
declare function faceValue<T>(value: T, props?: FaceValueProps): FaceValue<T>;

/**
 * The Timer class uses a requestAnimationFrame loop to build a timer that can
 * start and stop.
 *
 * @public
 */
declare class Timer {
    /**
     * The count increments with each interval.
     *
     * @protected
     */
    protected $count: number;
    /**
     * The requestAnimationFrame handle number.
     *
     * @protected
     */
    protected $handle?: number;
    /**
     * The number of milliseconds that define an interval.
     *
     * @public
     */
    readonly interval: number;
    /**
     * The timestamp of the last loop.
     *
     * @protected
     */
    protected $lastLoop?: number;
    /**
     * The date the timer starts.
     *
     * @protected
     */
    protected $startDate?: Date;
    /**
     * Construct the timer.
     *
     * @public
     */
    constructor(ms?: number);
    /**
     * Get the number of times the timer has ticked.
     *
     * @public
     */
    get count(): number;
    /**
     * The `elapsed` attribute.
     *
     * @public
     */
    get elapsed(): number;
    /**
     * The `elapsedSinceLastLoop` attribute.
     *
     * @public
     */
    get elapsedSinceLastLoop(): number;
    /**
     * Determines if the Timer is currently running.
     *
     * @public
     */
    get isRunning(): boolean;
    /**
     * Determines if the Timer is currently stopped.
     *
     * @public
     */
    get isStopped(): boolean;
    /**
     * Get the last timestamp the timer looped.
     *
     * @public
     */
    get lastLoop(): number;
    /**
     * Set the last timestamp the timer looped.
     *
     * @public
     */
    set lastLoop(value: number);
    /**
     * Get the date object when the timer started.
     *
     * @public
     */
    get started(): Date | undefined;
    /**
     * Resets the timer. If a callback is provided, re-start the clock.
     *
     * @public
     */
    reset(fn?: (timer: Timer) => void): Timer;
    /**
     * Starts the timer.
     *
     * @public
     */
    start(fn?: (timer: Timer) => void): Timer;
    /**
     * Stops the timer.
     *
     * @public
     */
    stop(fn?: (timer: Timer) => void): Timer;
}
/**
 * Create a new `Timer` instance.
 *
 * @public
 */
declare function timer(interval?: number): Timer;

/**
 * The dispose function.
 *
 * @public
 */
type DisposeFunction = () => void;
/**
 * A FlipClock theme definition.
 *
 * @public
 */
type Theme<T extends Face<T>> = {
    render: (el: Element, instance: FlipClock<T>) => [Element, DisposeFunction];
} & FaceHooks<T>;
/**
 * The options for `FlipClock`.
 *
 * @public
 */
type FlipClockProps<T extends Face<T>> = {
    /**
     * Automatically start the clock after it is mounted.
     */
    autoStart?: boolean;
    /**
     * The face displayed on the clock.
     */
    face: T;
    /**
     * The theme used to render the clock/
     */
    theme: Theme<T>;
    /**
     * The timer that controls the clock interval.
     */
    timer?: Timer | number;
    /**
     * The DOM element the clock is mounted.
     */
    parent?: Element | null;
};
/**
 * The FlipClock class starts, stops, resets, mounts, and unmounts the clock.
 * The clock also tracks the time and renders the clock with each interval.
 *
 * @public
 */
declare class FlipClock<T extends Face<T>> extends EventEmitter<Face<T>> {
    /**
     * Determines if the clock should automatically start when it is mounted.
     *
     * @public
     */
    readonly autoStart: boolean;
    /**
     * The parent element to which the clock is mounted.
     *
     * @public
     */
    parent?: Element;
    /**
     * The clock element.
     *
     * @public
     */
    el?: Element;
    /**
     * The face used to display the clock.
     *
     * @public
     */
    readonly face: T;
    /**
     * The face used to display the clock.
     *
     * @public
     */
    readonly theme: Theme<T>;
    /**
     * The face value displayed on the clock.
     *
     * @public
     */
    readonly timer: Timer;
    /**
     * Dispose of the clock.
     *
     * @private
     */
    protected dispose?: DisposeFunction;
    /**
     * Construct the FlipClock.
     *
     * @public
     */
    constructor(props: FlipClockProps<T>);
    /**
     * Get the animation rate of the clock.
     *
     * @public
     */
    get animationRate(): number;
    /**
     * Mount the clock instance to the DOM.
     *
     * @public
     */
    mount(parent: Element): this;
    /**
     * Start the clock instance.
     *
     * @public
     */
    start(fn?: (instance: FlipClock<T>) => void): this;
    /**
     * Stop the clock instance.
     *
     * @public
     */
    stop(fn?: (instance: FlipClock<T>) => void): this;
    /**
     * Toggle starting/stopping the clock instance.
     *
     * @public
     */
    toggle(fn?: (instance: FlipClock<T>) => void): this;
    /**
     * Unmount the clock instance from the DOM.
     *
     * @public
     */
    unmount(): this;
    /**
     * Dispatch the event and call the method that corresponds to given hook.
     *
     * @protected
     */
    protected hook<K extends keyof Required<FaceHooks<T>>>(key: K, ...args: Required<FaceHooks<T>>[K] extends (...args: infer P) => void ? P : any[]): void;
}
/**
 * Create a new `FlipClock` instance.
 *
 * @public
 */
declare function flipClock<T extends Face<T>>(props: FlipClockProps<T>): FlipClock<T>;

/**
 * The hooks that are fired during the lifecycle. Hooks are triggered in the
 * order they are defined. Hooks may be implemented on a `Face`, `Theme`, or
 * as an event.
 *
 * @public
 */
interface FaceHooks<T extends Face<T>> {
    /**
     * The `afterCreate` hook.
     *
     * @public
     */
    afterCreate?(instance: FlipClock<T>): void;
    /**
     * The `beforeMount` hook.
     *
     * @public
     */
    beforeMount?(instance: FlipClock<T>): void;
    /**
     * The `afterMount` hook.
     *
     * @public
     */
    afterMount?(instance: FlipClock<T>): void;
    /**
     * The `beforeUnmount` hook.
     *
     * @public
     */
    beforeUnmount?(instance: FlipClock<T>): void;
    /**
     * The `afterUnmount` hook.
     *
     * @public
     */
    afterUnmount?(instance: FlipClock<T>): void;
    /**
     * The `beforeInterval` hook.
     *
     * @public
     */
    beforeInterval?(instance: FlipClock<T>): void;
    /**
     * The `afterInterval` hook.
     *
     * @public
     */
    afterInterval?(instance: FlipClock<T>): void;
    /**
     * The `beforeStart` hook.
     *
     * @public
     */
    beforeStart?(instance: FlipClock<T>): void;
    /**
     * The `afterStart` hook.
     *
     * @public
     */
    afterStart?(instance: FlipClock<T>): void;
    /**
     * The `beforeStop` hook.
     *
     * @public
     */
    beforeStop?(instance: FlipClock<T>): void;
    /**
     * The `afterStop` hook.
     *
     * @public
     */
    afterStop?(instance: FlipClock<T>): void;
}
/**
 * All faces must implement this interface.
 *
 * @public
 */
declare interface Face<T extends Face<T> = any> extends FaceHooks<T> {
    /**
     * The face's value to display. When this value changes, or a new
     * `FaceValue` instance has been returned, the clock will automatically
     * re-render.
     *
     * @public
     */
    faceValue(): FaceValue<any>;
    /**
     * This method is called with every timer interval. Use this to increment,
     * decrement or value change the `faceValue()`.
     *
     * @public
     */
    interval(instance: FlipClock<T>): void;
}

/**
 * Get a range of numbers using the given size and starting point.
 *
 * @public
 */
declare function range(startAt: number | undefined, size: number): number[];
/**
 * Generates a random array of characters using the given range.
 *
 * @public
 */
declare function characterRange(startChar: string, endChar: string): string[];
/**
 * Shuffles array in place.
 *
 * @public
 */
declare function fisherYatesShuffle(chars: string[]): string[];
/**
 * Get the default character set.
 *
 * @public
 */
declare function defaultCharset(): string[];
/**
 * The options for `useCharset()`.
 *
 * @public
 */
type UseCharsetOptions = {
    /**
     * A function that returns an array of characters.
     */
    charset?: () => string[];
    /**
     * The empty character. Defaults to a space.
     */
    emptyChar?: string;
    /**
     * Provide a shuffle function `boolean` to enable/disable the default shuffle.
     */
    shuffle?: ((chars: string[]) => string[]) | boolean;
    /**
     * An array of characters to omit from the `charset`.
     */
    blacklist?: string[];
    /**
     * An array of characters to include in the `charset`.
     */
    whitelist?: string[];
};
/**
 * The return type for `useCharset()`.
 *
 * @public
 */
type UseCharset = {
    /**
     * The charset that was given.
     */
    charset: string[];
    /**
     * The empty character from the charset.
     */
    emptyChar: string;
    /**
     * Determines if the given value is blacklisted.
     */
    isBlacklisted: (value: DigitizedValue) => boolean;
    /**
     * Determines if the given value is whitelisted.
     */
    isWhitelisted: (value: DigitizedValue) => boolean;
    /**
     * Get a chunk of the charset for the given count.
     */
    chunk: (value: DigitizedValue | undefined, count: number) => string[];
    /**
     * Gets the next characters in the charset for the given count.
     */
    next: (value?: DigitizedValue, target?: DigitizedValue | DigitizedValues, count?: number) => DigitizedValue | undefined;
    /**
     * Gets the previous characters in the charset for the given count.
     */
    prev: (value?: DigitizedValue, target?: DigitizedValue | DigitizedValues, count?: number) => DigitizedValue | undefined;
};
/**
 * A composable that uses a set of characters to create a charset.
 *
 * @public
 */
declare function useCharset(): UseCharset;
declare function useCharset(options: UseCharsetOptions): UseCharset;
declare function useCharset(options?: UseCharsetOptions): UseCharset;

/**
 * The options for matchArrayStructure().
 *
 * @public
 */
type MatchArrayStructureOptions = {
    backwards?: boolean;
};
/**
 * The callback for matchArrayStructure().
 *
 * @public
 */
type MatchArrayStructureCallback = Callback<[value?: DigitizedValue, target?: DigitizedValue | DigitizedValues], DigitizedValue | undefined>;
/**
 * Match the structure of the current value to the target.
 *
 * @public
 */
declare function matchArrayStructure(current: DigitizedValues, target: DigitizedValues, fn?: MatchArrayStructureCallback): DigitizedValues;
declare function matchArrayStructure(current: DigitizedValues, target: DigitizedValues, options: MatchArrayStructureOptions | undefined, fn?: MatchArrayStructureCallback): DigitizedValues;
/**
 * Cast a value to a string.
 *
 * @public
 */
declare function castDigitizedString(value?: DigitizedValue | DigitizedValues): DigitizedValue | undefined;
/**
 * Cast a value to an array of strings.
 *
 * @public
 */
declare function castDigitizedValues(value?: DigitizedValue | DigitizedValues): DigitizedValue[];
/**
 * Cast a value to a array of digitized arrays.
 *
 * @public
 */
declare function castDigitizedGroup(value?: DigitizedValue | DigitizedValues): DigitizedValues;
/**
 * Determines if the value is a digitized group, which is an array of digitized
 * values.
 *
 * @public
 */
declare function isDigitizedGroup(value: DigitizedValues | DigitizedValue | undefined): boolean;
/**
 * Counts the digits recursively.
 *
 * @public
 */
declare function count(values: DigitizedValues): number;
type Callback<P extends CallbackParams<any[]>, R = undefined> = (...args: P) => R;
type CallbackParams<T> = T extends any[] ? T : never;
/**
 * A change object that tracks changes within an iterator.
 *
 * @public
 */
type Change<R> = {
    from: R;
    to: R;
};
/**
 * A readonly object that when returned will stop an iterator.
 */
type Stop = Readonly<{
    stop: true;
}>;
/**
 * Utility function to stop an iterator.
 *
 * @public
 */
declare function stop(): Stop;
/**
 * Call for for `trackChanges()`.
 *
 * @public
 */
type TrackChangesCallback<P extends any[], R, C = P[0] | undefined> = (changes: Change<C>[], ...args: P) => R | Stop;
/**
 * Create a callback with the values that can be tracked.
 *
 * @public
 */
declare function trackChanges<P extends any[], R>(fn: TrackChangesCallback<P, R>): Callback<P, R>;
/**
 * Determines if a iterator should stop.
 *
 * @public
 */
type StopPredicateFunction<T extends CallbackParams<any[]> = any[]> = TrackChangesCallback<T, boolean>;
/**
 * Stop the walker using a predicate function. Return `false` to stop and `true`
 * to continue. The predicate is ran before the callback function.
 *
 * @public
 */
declare function stopWhen<P extends CallbackParams<any[]>, R>(predicate: StopPredicateFunction<P>, fn: Callback<P, R>): Callback<P, R>;
/**
 * Stop the walker after X number of changes.
 *
 * @public
 */
declare function stopAfterChanges<P extends CallbackParams<any[]>, R>(totalChanges: number, fn: Callback<P, R>): Callback<P, R>;

/**
 * The options for `useSequencer()`.
 *
 * @public
 */
type SequencerOptions = {
    /**
     * The charset instance or options used to generate a charset.
     */
    charset?: UseCharset | UseCharsetOptions;
    /**
     * The options passed the function that ensure the array structures are the same.
     */
    matchArray?: MatchArrayStructureOptions;
    /**
     * A call that determines when the sequencer should stop.
     */
    stopWhen?: StopPredicateFunction<[current?: DigitizedValue, target?: DigitizedValue | DigitizedValues]>;
    /**
     * A number of changes that stops the sequencer.
     */
    stopAfterChanges?: number;
};
/**
 * The return type for `useSequencer()`.
 *
 * @public
 */
type UseSequencer = {
    /**
     * The charset used by the sequencer.
     */
    charset: string[];
    /**
     * Decrement the current value towards the target value.
     */
    decrement: (current: FaceValue<any>, target: FaceValue<any>, count?: number, backwards?: boolean) => FaceValue<any>;
    /**
     * Increment the current value towards the target value.
     */
    increment: (current: FaceValue<any>, target: FaceValue<any>, count?: number, backwards?: boolean) => FaceValue<any>;
};
/**
 * A composable that creates or uses a charset to increment and decrement
 * face values.
 *
 * @public
 */
declare function useSequencer(): UseSequencer;
declare function useSequencer(options: SequencerOptions): UseSequencer;
declare function useSequencer(options?: SequencerOptions): UseSequencer;

/**
 * The `Alphanumeric` face options.
 *
 * @public
 */
type AlphanumericProps = {
    /**
     * The starting value of the clock.
     */
    value: FaceValue<string> | FaceValue<DigitizedValues>;
    /**
     * The target value of the clock.
     */
    targetValue?: FaceValue<string> | FaceValue<DigitizedValues>;
    /**
     * Determines if the clock increments or decrements towards the target.
     */
    method?: 'increment' | 'decrement';
    /**
     * Determines if the sequencer works forwards or backwards.
     */
    direction?: 'auto' | 'forwards' | 'backwards';
    /**
     * The sequencer instance or options used for the sequencer.
     */
    sequencer?: UseSequencer | SequencerOptions;
    /**
     * Determines how many characters to skip with each interval.
     */
    skipChars?: number;
};
/**
 * This face is designed to flip through alphanumeric values similar to a flip
 * board at a train station. The value will incrementally/decrementally flip
 * the digits until it reaches the target.
 *
 * @public
 */
declare class Alphanumeric implements Face {
    /**
     * The sequencer method.
     *
     * @public
     */
    readonly method: 'increment' | 'decrement';
    /**
     * The flip direction. If auto, the direction is automatically determined
     * based on the current value and target value.
     *
     * @public
     */
    readonly direction: 'auto' | 'forwards' | 'backwards';
    /**
     * Override how digits are sequenced.
     *
     * @public
     */
    readonly sequencer: UseSequencer;
    /**
     * The number of characters to skip during the incrementing/decrementing.
     *
     * @public
     */
    skipChars?: number;
    /**
     * The face's current value.
     *
     * @public
     */
    readonly value: FaceValue<string> | FaceValue<DigitizedValues>;
    /**
     * The face's target value.
     *
     * @public
     */
    readonly targetValue: FaceValue<string> | FaceValue<DigitizedValues>;
    /**
     * The face's current value.
     *
     * @protected
     */
    protected currentValue: FaceValue<DigitizedValues>;
    /**
     * Construct the clock face.
     *
     * @public
     */
    constructor(props: AlphanumericProps);
    /**
     * The sequencer method to call.
     *
     * @public
     */
    get backwards(): boolean;
    /**
     * The face's current value.
     *
     * @public
     */
    faceValue(): FaceValue<any>;
    /**
     * This method is called with every interval, or every time the clock
     * should change, and handles the actual incrementing and decrementing the
     * clock's `FaceValue`.
     *
     * @public
     */
    interval(instance: FlipClock<Alphanumeric>): void;
    /**
     * Increment the value to the next sequence.
     *
     * @public
     */
    increment(): void;
    /**
     * Decrement the value to the next sequence.
     *
     * @public
     */
    decrement(): void;
}
/**
 * Create a new `Alphanumeric` instance.
 *
 * @public
 */
declare function alphanumeric(props: AlphanumericProps): Alphanumeric;

type UseDefinitionMap<T> = {
    /**
     * A map of key/value pairs.
     */
    map: Map<string, T>;
    /**
     * Define a new definition.
     */
    define(key: string, value: T): void;
    define(key: [string, T][]): void;
    define(key: Record<string, T>): void;
    define(key: string | [string, T][] | Record<string, T>, value?: T): void;
    /**
     * Removes a definition.
     */
    unset(keys: string): void;
    unset(keys: string[]): void;
    unset(keys: string | string[]): void;
};
type InferType<T> = T extends [string, infer V][] ? V : never;
declare function useDefinitionMap<T extends [string, unknown][]>(items: T): UseDefinitionMap<InferType<T>>;
declare function useDefinitionMap<T>(items: Record<string, T>): UseDefinitionMap<T>;
/**
 * The translator function.
 */
type Translator<T, K = string> = (value: K) => T;
/**
 * The return type for `useDictionary()`.
 *
 * @public
 */
type UseDictionary<T, K = string> = UseDefinitionMap<T | Translator<T>> & {
    /**
     * Translate a key. If no key is found, use the fallback.
     */
    translate(key: K): T;
    translate(key: K, fallback: T): T;
    translate(key: K, fallback?: T): T;
};
/**
 * Use the provided terms to create a reusable translation dictionary.
 *
 * @public
 */
declare function useDictionary<T>(terms: [string, T | Translator<T>][]): UseDictionary<T>;
declare function useDictionary<T>(terms: Record<string, T | Translator<T>>): UseDictionary<T>;

/**
 * The number of days in a week.
 *
 * @public
 */
declare const daysInWeek: number;
/**
 * The number of milliseconds in 1 day.
 *
 * @public
 */
declare const millisecondsInDay: number;
/**
 * The number of milliseconds in 1 hour.
 *
 * @public
 */
declare const millisecondsInHour: number;
/**
 * The number of milliseconds in 1 minute.
 *
 * @public
 */
declare const millisecondsInMinute: number;
/**
 * The proper names of the days in English.
 *
 * @public
 */
declare const days: string[];
/**
 * The abbreviated names of the days in English.
 *
 * @public
 */
declare const dayAbbreviations: string[];
/**
 * The proper names of the months in English.
 *
 * @public
 */
declare const months: string[];
/**
 * The abbreviated names of the months in English.
 *
 * @public
 */
declare const monthAbbreviations: string[];
/**
 * Formats a date into a string.
 *
 * @public
 */
type DateFlagFormatFunction = (date: Date) => string;
/**
 * The options for `useDateFormats()`.
 *
 * @public
 */
type UseDateFormatsOptions = {
    /**
     * The digitizer instance.
     */
    digitizer?: UseDigitizer;
    /**
     * A translate function or Dictionary.
     */
    translate?: Translator<string> | UseDictionary<string>;
    /**
     * The date format flags.
     */
    formats?: Record<string, DateFlagFormatFunction>;
};
/**
 * The return type for `useDateFormats()`.
 *
 * @public
 */
type UseDateFormats = UseDefinitionMap<DateFlagFormatFunction> & {
    format: (date: Date, format: string) => string;
};
/**
 * Create a new date string formatter.
 *
 * @public
 */
declare function useDateFormats(): UseDateFormats;
declare function useDateFormats(options: UseDateFormatsOptions): UseDateFormats;
/**
 * So an array based on the index position of another.
 *
 * @public
 */
declare function sort(map: Map<string, unknown>): string[];
/**
 * Left pad another value with zero if its less then the given length.
 *
 * @public
 */
declare function pad(value: string | number | undefined, length: number): string;
/**
 * Get the twelve hour format of the current date.
 *
 * @public
 */
declare function getTwelveHourFormat(date: Date): string;

/**
 * The `Clock` face options.
 *
 * @public
 */
type ClockProps = {
    /**
     * Specify a date used to start the display on the clock.
     */
    date?: Date;
    /**
     * A format string for how the date is displayed.
     */
    format?: string;
    /**
     * A formatter to display the date in the given format.
     */
    formatter?: UseDateFormats | UseDateFormatsOptions;
};
/**
 * This face will show a clock in a given format. *
 *
 * @public
 */
declare class Clock implements Face {
    /**
     * The starting date on the clock. If no date is set, the current time
     * will be used.
     *
     * @public
     */
    readonly date: Date;
    /**
     * The current formatted value.
     *
     * @public
     */
    readonly value: FaceValue<string>;
    /**
     * The format string.
     *
     * @public
     */
    format: string;
    /**
     * The duration formatter.
     *
     * @public
     */
    formatter: UseDateFormats;
    /**
     * Instantiate the clock face.
     *
     * @public
     */
    constructor(props?: ClockProps);
    /**
     * The face's current value.
     *
     * @public
     */
    faceValue(): FaceValue<string>;
    /**
     * Format the face value to the current date/time.
     *
     * @public
     */
    interval(instance: FlipClock<Clock>): void;
}
/**
 * Create a new `Clock` instance.
 *
 * @public
 */
declare function clock(props?: ClockProps): Clock;

/**
 * The `Counter` face options.
 *
 * @public
 */
type CounterProps = {
    /**
     * Determines if a clock should count down instead of up.
     */
    countdown?: boolean;
    /**
     * A format function for how the counter is displayed.
     */
    format?: (value: number) => string;
    /**
     * A number formatter for how the counter is displayed.
     */
    formatter?: Intl.NumberFormat;
    /**
     * The starting value of the counter.
     */
    value?: FaceValue<number> | number;
    /**
     * The number of steps the counter ticks each interval.
     */
    step?: number;
    /**
     * The clock will automatically stop when the target value is reached.
     */
    targetValue?: FaceValue<number> | number;
};
/**
 * This face is designed to increment and decrement values. Usually this face
 * is used as a counter for 0, 1, 2, 3, 4 (etc) for something like page views.
 *
 * @public
 */
declare class Counter implements Face {
    /**
     * Should the face count down instead of up.
     *
     * @public
     */
    countdown: boolean;
    /**
     * The number to increment/decrement in the interval.
     *
     * @public
     */
    step: number;
    /**
     * The formatted face value to display on the clock.
     *
     * @protected
     */
    protected formattedValue: FaceValue<string>;
    /**
     * The target value determines when the counter should stop.
     *
     * @public
     */
    targetValue?: FaceValue<number>;
    /**
     * The current face value.
     *
     * @public
     */
    value: FaceValue<number>;
    /**
     * A format callback. If the `formatter` is defined, this prop is ignored.
     *
     * @public
     */
    format?: (number: number) => string;
    /**
     * An `Intl.NumberFormat` instance used to format the number into a string.
     *
     * @public
     */
    formatter?: Intl.NumberFormat;
    /**
     * Construct the clock face.
     *
     * @public
     */
    constructor(props?: CounterProps);
    /**
     * Get the number as a formatted string.
     *
     * @public
     */
    get formattedString(): string;
    /**
     * The face's current value.
     *
     * @public
     */
    faceValue(): FaceValue<string>;
    /**
     * This method is called with every interval, or every time the clock
     * should change, and handles the actual incrementing and decrementing the
     * clock's `FaceValue`.
     *
     * @public
     */
    interval(instance: FlipClock<Counter>): void;
    /**
     * Substract the face value by the given value.
     *
     * @public
     */
    decrement(value?: number): void;
    /**
     * Add to the face value by the given value.
     *
     * @public
     */
    increment(value?: number): void;
}
/**
 * Create a new `Counter` instance.
 *
 * @public
 */
declare function counter(props?: CounterProps): Counter;

/**
 * The duration flag format function.
 *
 * @public
 */
type DurationFlagFormatter = (duration: Duration, length: number) => string;
/**
 * The duration map definition.
 *
 * @public
 */
type DurationMapDefinition = [keyof Duration, DurationFlagFormatter];
/**
 * Get duration between two dates with only specified keys
 *
 * @public
 */
declare function getFilteredDuration<T extends keyof Duration>(start: Date | number, end: Date | number, keys: T[]): Pick<Duration, T>;
/**
 * The return type for `useDurationFormats()`.
 *
 * @public
 */
type UseDurationFormats = {
    /**
     * Format the start and end date into a string.
     */
    format: (start: Date, end: Date, format: string) => string;
};
declare function useDurationFormats(): UseDurationFormats;

/**
 * The `ElapsedTime` face options.
 *
 * @public
 */
type ElapsedTimeProps = {
    /**
     * The date from which the elapsed time is calculated.
     */
    from?: Date;
    /**
     * The date to which the elapsed time is calculated.
     */
    to?: Date;
    /**
     * A format string for how the duration is displayed.
     */
    format?: string;
    /**
     * A formatter to display the duration in the given format.
     */
    formatter?: UseDurationFormats;
};
/**
 * This face will show the amount of time elapsed since the given value and
 * display it a specific format. For example 'hh:mm:ss' will show the elapsed
 * time in hours, minutes, seconds.
 *
 * @public
 */
declare class ElapsedTime implements Face {
    /**
     * The date used to calculate the current.
     *
     * @protected
     */
    protected start: Date;
    /**
     * The date used to calculate the current.
     *
     * @protected
     */
    protected current: Date;
    /**
     * The "from" date used to calculate the elsapsed time.
     *
     * @public
     */
    from?: Date;
    /**
     * The "to" date used to calculate the elsapsed time.
     *
     * @public
     */
    to?: Date;
    /**
     * The format string.
     *
     * @public
     */
    format: string;
    /**
     * The duration formatter.
     *
     * @public
     */
    formatter: UseDurationFormats;
    /**
     * The current face value.
     *
     * @public
     */
    value: FaceValue<string>;
    /**
     * Construct the clock face.
     *
     * @public
     */
    constructor(props?: ElapsedTimeProps);
    /**
     * Get the elapsed time as a formatted string.
     *
     * @public
     */
    get formattedString(): string;
    /**
     * The face's current value.
     *
     * @public
     */
    faceValue(): FaceValue<string>;
    /**
     * Format the value with the new elapsed time.
     *
     * @public
     */
    interval(instance: FlipClock<ElapsedTime>): void;
    /**
     * Set the dates before the clock starts.
     *
     * @public
     */
    beforeStart(): void;
    /**
     * Determines if the clock should be stopped.
     *
     * @public
     */
    shouldStop(): boolean;
}
/**
 * Create a new `ElapsedTime` instance.
 *
 * @public
 */
declare function elapsedTime(props?: ElapsedTimeProps): ElapsedTime;

/**
 * A CSS-in-JS style object.
 *
 * @public
 */
interface CSSProperties extends Properties {
    [key: string]: CSSProperties | string | number | undefined | null;
}
/**
 * Merge the target object into the source.
 *
 * @public
 */
declare function mergeCss<TSource extends CSSProperties, TTarget extends CSSProperties>(source: TSource, target: TTarget): TSource;
type MergedCssDeclaration<T, U> = {
    [K in keyof T | keyof U]: K extends keyof U ? U[K] : K extends keyof T ? T[K] : never;
};
type CssDeclaration<T extends CSSProperties = CSSProperties> = {
    css: T;
    toString(): string;
};
type UseCssDeclaration<T extends readonly unknown[], V extends CSSProperties> = (...args: T) => V;
type UseCss<T extends readonly unknown[] = unknown[], V extends CSSProperties = CSSProperties> = {
    /**
     * Get the CSS declaration.
     */
    (...args: T): CssDeclaration<V>;
    /**
     * Merge the given CSS into the current definition.
     */
    merge: <TExtension extends CSSProperties>(fn: UseCssDeclaration<T, TExtension>) => UseCss<T, MergedCssDeclaration<V, TExtension>>;
    /**
     * Extend the current definition with the given CSS.
     */
    extend: <TExtension extends CSSProperties>(fn: UseCssDeclaration<T, TExtension>) => UseCss<T, MergedCssDeclaration<V, TExtension>>;
};
declare function useCss<T extends readonly unknown[], V extends CSSProperties>(fn: UseCssDeclaration<T, V>): UseCss<T, V>;

declare function parseDuration(duration: string | null | undefined): number;
declare function getAnimationRate(el: Element): number;

/** Provides information pointing to a location within a source. */
interface Location {
  /** Line in the parsed source (1-based). */
  readonly line: number;
  /** Column in the parsed source (1-based). */
  readonly column: number;
  /** Offset in the parsed source (0-based). */
  readonly offset: number;
}

/**
 * Anything that can successfully be converted to a string with `String()`
 * so that it can be used in error messages.
 *
 * The GrammarLocation class in Peggy is a good example.
 */
interface GrammarSourceObject {
  readonly toString: () => string;

  /**
   * If specified, allows the grammar source to be embedded in a larger file
   * at some offset.
   */
  readonly offset?: undefined | ((loc: Location) => Location);
}

/**
 * Most often, you just use a string with the file name.
 */
type GrammarSource = string | GrammarSourceObject;

/** The `start` and `end` position's of an object within the source. */
interface LocationRange {
  /**
   * A string or object that was supplied to the `parse()` call as the
   * `grammarSource` option.
   */
  readonly source: GrammarSource;
  /** Position at the beginning of the expression. */
  readonly start: Location;
  /** Position after the end of the expression. */
  readonly end: Location;
}

/**
 * Expected a literal string, like `"foo"i`.
 */
interface LiteralExpectation {
  readonly type: "literal";
  readonly text: string;
  readonly ignoreCase: boolean;
}

/**
 * Range of characters, like `a-z`
 */
type ClassRange = [
  start: string,
  end: string,
]

interface ClassParts extends Array<string | ClassRange> {
}

/**
 * Expected a class, such as `[^acd-gz]i`
 */
interface ClassExpectation {
  readonly type: "class";
  readonly parts: ClassParts;
  readonly inverted: boolean;
  readonly ignoreCase: boolean;
}

/**
 * Expected any character, with `.`
 */
interface AnyExpectation {
  readonly type: "any";
}

/**
 * Expected the end of input.
 */
interface EndExpectation {
  readonly type: "end";
}

/**
 * Expected some other input.  These are specified with a rule's
 * "human-readable name", or with the `expected(message, location)`
 * function.
 */
interface OtherExpectation {
  readonly type: "other";
  readonly description: string;
}

type Expectation =
  | AnyExpectation
  | ClassExpectation
  | EndExpectation
  | LiteralExpectation
  | OtherExpectation;

/**
 * Pass an array of these into `SyntaxError.prototype.format()`
 */
interface SourceText {
  /**
   * Identifier of an input that was used as a grammarSource in parse().
   */
  readonly source: GrammarSource;
  /** Source text of the input. */
  readonly text: string;
}

declare class SyntaxError extends globalThis.SyntaxError {
    /**
   * Constructs the human-readable message from the machine representation.
   *
   * @param expected Array of expected items, generated by the parser
   * @param found Any text that will appear as found in the input instead of
   *   expected
   */
    static buildMessage(expected: Expectation[], found?: string | null | undefined): string;
    readonly expected: Expectation[];
    readonly found: string | null | undefined;
    readonly location: LocationRange;
    readonly name: string;
    constructor(
    message: string,
    expected: Expectation[],
    found: string | null,
    location: LocationRange,
  );

    /**
   * With good sources, generates a feature-rich error message pointing to the
   * error in the input.
   * @param sources List of {source, text} objects that map to the input.
   */
    format(sources: SourceText[]): string;
}

/**
 * Trace execution of the parser.
 */
interface ParserTracer {
  trace: (event: ParserTracerEvent) => void;
}

type ParserTracerEvent
  = {
      readonly type: "rule.enter";
      readonly rule: string;
      readonly location: LocationRange
    }
  | {
      readonly type: "rule.fail";
      readonly rule: string;
      readonly location: LocationRange
    }
  | {
      readonly type: "rule.match";
      readonly rule: string;
      readonly location: LocationRange
      /** Return value from the rule. */
      readonly result: unknown;
    };

type StartRuleNames = "array";
interface ParseOptions<T extends StartRuleNames = "array"> {
  /**
   * String or object that will be attached to the each `LocationRange` object
   * created by the parser. For example, this can be path to the parsed file
   * or even the File object.
   */
  readonly grammarSource?: GrammarSource;
  readonly startRule?: T;
  readonly tracer?: ParserTracer;

  // Internal use only:
  readonly peg$library?: boolean;
  // Internal use only:
  peg$currPos?: number;
  // Internal use only:
  peg$silentFails?: number;
  // Internal use only:
  peg$maxFailExpected?: Expectation[];
  // Extra application-specific properties
  [key: string]: unknown;
}

declare const StartRules: StartRuleNames[];
declare const parse: typeof ParseFunction;

// Overload of ParseFunction for each allowedStartRule

declare function ParseFunction<Options extends ParseOptions<"array">>(
  input: string,
  options?: Options,
): any;

declare function ParseFunction<Options extends ParseOptions<StartRuleNames>>(
  input: string,
  options?: Options,
): any;

/**
 * The FlipClock theme labels.
 *
 * @public
 *
 */
type FlipClockThemeLabels = (string | FlipClockThemeLabels)[];
/**
 * The FlipClock theme options.
 *
 * @public
 */
type FlipClockThemeOptions<T extends CssDeclaration = CssDeclaration> = {
    /**
     * The CSS declarations used for the theme.
     */
    css?: T | T[];
    /**
     * The characters that should be rendered as dividers.
     */
    dividers?: RegExp | string | string[];
    /**
     * The labels that appear above the groups.
     */
    labels?: FlipClockThemeLabels;
};
/**
 * Renders a FlipClock theme.
 *
 * @public
 */
declare function theme(): Theme<any>;
declare function theme<T extends CssDeclaration>(options: FlipClockThemeOptions<T>): Theme<any>;
declare function theme<T extends CssDeclaration>(options?: FlipClockThemeOptions<T>): Theme<any>;

/**
 * The FlipClock CSS options.
 *
 * @public
 */
type FlipClockCssOptions = {
    borderRadius?: string;
    fontSize?: string;
    fontFamily?: string;
    width?: string;
    height?: string;
    animationDuration?: string;
    animationDelay?: string;
};
/**
 * The FlipClock Theme CSS.
 *
 * @public
 */
declare const css: UseCss<[options?: FlipClockCssOptions | undefined], {
    '&': {
        '--border-radius': string;
        '--font-size': string;
        '--font-family': string;
        '--width': string;
        '--height': string;
        '--animation-duration': string;
        '--animation-delay': string;
        fontFamily: "var(--font-family)";
        fontSize: "var(--font-size)";
        userSelect: "none";
        textAlign: "center";
        position: "relative";
        width: "100%";
        display: "inline-flex";
        boxSizing: "border-box";
        alignItems: "flex-end";
        gap: ".25rem";
    };
    '.flip-clock-label': {
        fontSize: "1rem";
        marginBottom: ".5rem";
    };
    '.flip-clock-meridium': {
        lineHeight: "1em";
        top: "50%";
        left: "100%";
        flex: "0";
        width: "auto";
        textTransform: "uppercase";
        fontWeight: "200";
        transform: "translate(.5em, -50%)";
    };
    '.flip-clock-divider': {
        position: "relative";
        display: "flex";
        alignItems: "center";
        justifyContent: "center";
        fontFamily: "serif";
        color: "#333";
        height: "var(--height)";
        '.flip-clock-divider-inner': {
            fontSize: "1.25em";
        };
        '&[data-value=" "]': {
            minWidth: "1rem";
        };
        '.dark &': {
            color: "#ccc";
        };
    };
    '.flip-clock-group': {
        display: "flex";
        flexDirection: "column";
        '+ .flip-clock-group': {
            marginLeft: "1rem";
        };
        '.flip-clock-group-items': {
            display: "flex";
            alignItems: "end";
            gap: ".25rem";
        };
    };
    '.flip-clock-card': {
        width: "var(--width)";
        height: "var(--height)";
        position: "relative";
        borderRadius: "var(--border-radius)";
        boxShadow: "0 1.5px 3px rgba(0, 0, 0, 0.24), 0 3px 8px rgba(0, 0, 0, 0.05)";
        fontWeight: "bold";
        color: "#ccc";
        flexShrink: number;
        '&:not(.animate)': {
            '.active .flip-clock-card-item-inner': {
                zIndex: "4";
            };
            '.flip-clock-card-item-inner': {
                '.top, .bottom': {
                    '&:after': {
                        display: "none";
                    };
                };
            };
        };
        '.flip-clock-card-item': {};
        '.flip-clock-card-item-inner': {
            position: "absolute";
            width: "100%";
            height: "100%";
            '&:first-child': {
                zIndex: "2";
            };
            '.top, .bottom': {
                width: "100%";
                height: "50%";
                overflow: "hidden";
                position: "relative";
                fontSize: "1em";
                background: "#333";
                boxShadow: "inset 0 0 .2em rgba(0,0,0,.5)";
                '&:after': {
                    content: "\" \"";
                    display: "block";
                    position: "absolute";
                    top: "0";
                    right: "0";
                    bottom: "0";
                    left: "0";
                    overflow: "hidden";
                };
                '&:before': {
                    content: "\" \"";
                    display: "block";
                    width: "100%";
                    height: "1px";
                    position: "absolute";
                };
            };
            '.top': {
                borderRadius: "var(--border-radius) var(--border-radius) 0 0";
                lineHeight: "var(--height)";
                '&:after': {
                    borderRadius: "var(--border-radius) var(--border-radius) 0 0";
                };
                '&:before': {
                    background: "#333";
                    opacity: ".4";
                    bottom: "0";
                };
            };
            '.bottom': {
                borderRadius: "0 0 var(--border-radius) var(--border-radius)";
                lineHeight: "0";
                '&:after': {
                    borderRadius: "0 0 var(--border-radius) var(--border-radius)";
                };
                '&:before': {
                    background: "#ccc";
                    opacity: ".1";
                };
            };
        };
        '&.animate': {
            animationDuration: "var(--animation-duration)";
            animationDelay: "var(--animation-delay)";
            '.flip-clock-card-item-inner': {
                perspective: "15em";
            };
            '.top, .bottom, .active, .active > div, .before, .before > div': {
                animationDelay: "inherit";
                animationFillMode: "forwards";
                animationDuration: "inherit";
                animationTimingFunction: "inherit";
                '&:after': {
                    animationDuration: "inherit";
                    animationFillMode: "inherit";
                };
            };
            '.before': {
                animationDelay: "0s";
                animationTimingFunction: "ease-in";
                '.top': {
                    animationName: "flip-clock-top";
                };
                '.top:after, .bottom:after': {
                    animationName: "flip-clock-show-shadow";
                };
            };
            '.active': {
                animationTimingFunction: "ease-out";
                '& > div': {
                    animationName: "flip-clock-indexing";
                };
                '.top:after, .bottom:after': {
                    animationName: "flip-clock-hide-shadow";
                };
                '.bottom': {
                    animationName: "flip-clock-bottom";
                };
            };
        };
        '.active': {
            zIndex: "2";
            '.bottom': {
                zIndex: "2";
                transformOrigin: "top center";
            };
        };
        '.before': {
            zIndex: "3";
            '.top': {
                zIndex: "2";
                transformOrigin: "bottom center";
                '&:after': {
                    background: "linear-gradient(to bottom, rgba(0,0,0,.1) 0%, rgba(0,0,0,1) 100%)";
                };
            };
            '.bottom': {
                '&:after': {
                    background: "linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(0,0,0,.1) 100%)";
                };
            };
        };
    };
    '@keyframes flip-clock-indexing': {
        '0%': {
            zIndex: "2";
        };
        '1%': {
            zIndex: "3";
        };
        '100%': {
            zIndex: "4";
        };
    };
    '@keyframes flip-clock-bottom': {
        '0%': {
            transform: "rotateX(90deg)";
        };
        '100%': {
            transform: "rotateX(0)";
        };
    };
    '@keyframes flip-clock-top': {
        '0%': {
            transform: "rotateX(0)";
        };
        '100%': {
            transform: "rotateX(-90deg)";
        };
    };
    '@keyframes flip-clock-show-shadow': {
        '0%': {
            opacity: "0";
        };
        '100%': {
            opacity: "1";
        };
    };
    '@keyframes flip-clock-hide-shadow': {
        '0%': {
            opacity: "1";
        };
        '100%': {
            opacity: "0";
        };
    };
}>;

export { Alphanumeric, type AlphanumericProps, type AnyExpectation, type CSSProperties, type Callback, type CallbackParams, type Change, type ClassExpectation, type ClassParts, type ClassRange, Clock, type ClockProps, Counter, type CounterProps, type CssDeclaration, type DateFlagFormatFunction, type DigitizedValue, type DigitizedValues, type DisposeFunction, type DurationFlagFormatter, type DurationMapDefinition, EMPTY_CHAR, ElapsedTime, type ElapsedTimeProps, type EndExpectation, type Event, EventEmitter, type EventEmitterCallback, type Expectation, type Face, type FaceHooks, FaceValue, type FaceValueProps, FlipClock, type FlipClockCssOptions, type FlipClockProps, type FlipClockThemeLabels, type FlipClockThemeOptions, type GrammarSource, type GrammarSourceObject, type LiteralExpectation, type Location, type LocationRange, type MatchArrayStructureCallback, type MatchArrayStructureOptions, type MergedCssDeclaration, type OtherExpectation, type ParseOptions, type ParserTracer, type ParserTracerEvent, type SequencerOptions, type SourceText, type StartRuleNames, StartRules, type Stop, type StopPredicateFunction, SyntaxError, type Theme, Timer, type TrackChangesCallback, type Translator, type UseCharset, type UseCharsetOptions, type UseCss, type UseCssDeclaration, type UseDateFormats, type UseDateFormatsOptions, type UseDefinitionMap, type UseDictionary, type UseDigitizer, type UseDurationFormats, type UseSequencer, alphanumeric, castDigitizedGroup, castDigitizedString, castDigitizedValues, characterRange, clock, count, counter, css, dayAbbreviations, days, daysInWeek, defaultCharset, elapsedTime, eventEmitter, faceValue, fisherYatesShuffle, flipClock, getAnimationRate, getFilteredDuration, getTwelveHourFormat, isDigitizedGroup, matchArrayStructure, mergeCss, millisecondsInDay, millisecondsInHour, millisecondsInMinute, monthAbbreviations, months, pad, parse, parseDuration, range, sort, stop, stopAfterChanges, stopWhen, theme, timer, trackChanges, useCharset, useCss, useDateFormats, useDefinitionMap, useDictionary, useDigitizer, useDurationFormats, useSequencer };
