export type ServerSentEvent = {
    event: string | null;
    data: string;
    raw: string[];
};
export declare class Stream<Item> implements AsyncIterable<Item> {
    private iterator;
    controller: AbortController;
    constructor(iterator: () => AsyncIterator<Item>, controller: AbortController);
    static fromSSEResponse<Item>(response: any, controller: AbortController): Stream<Item>;
    /**
     * 从可读流中读取数据，并返回一个流对象
     *
     * @param readableStream 可读流
     * @param controller 控制器
     * @returns 返回一个流对象
     */
    static fromReadableStream<Item>(readableStream: ReadableStream, controller: AbortController): Stream<Item>;
    [Symbol.asyncIterator](): AsyncIterator<Item>;
    /**
     * 将一个流复制成两个流
     *
     * @returns 返回一个由两个流组成的元组
     */
    tee(): [Stream<Item>, Stream<Item>];
    /**
    * 将可迭代对象转换为可读流
    *
    * @returns 返回一个可读流
    */
    toReadableStream(): ReadableStream;
}
/**
 * 大多数浏览器尚未对 ReadableStream 提供异步可迭代支持，
 * 并且 Node.js 有一种非常不同的方式来从其 "ReadableStream" 中读取字节。
 *
 * 这个 polyfill 是从 https://github.com/MattiasBuelens/web-streams-polyfill/pull/122#issuecomment-1627354490 拉取的。
 */
export declare function readableStreamAsyncIterable<T>(stream: any): AsyncIterableIterator<T>;
