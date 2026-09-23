const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Offer = {
  market_id: number;
  market_name: string;
  price: number;
};

type Product = {
  id: number;
  name: string;
  unit: string;
  offers: Offer[];
};

async function getProducts(): Promise<Product[]> {
  const res = await fetch(`${API_URL}/products`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load products");
  return res.json();
}

export default async function Home() {
  const products = await getProducts();

  return (
    <div className="flex flex-col flex-1 items-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex w-full max-w-3xl flex-col gap-8 py-16 px-6">
        <h1 className="text-3xl font-semibold text-black dark:text-zinc-50">
          마트픽 — 품목별 최저가
        </h1>

        <div className="flex flex-col gap-4">
          {products.map((product) => {
            const [cheapest, ...rest] = product.offers;
            return (
              <div
                key={product.id}
                className="rounded-xl border border-black/[.08] bg-white p-5 dark:border-white/[.145] dark:bg-zinc-900"
              >
                <div className="flex items-baseline justify-between">
                  <h2 className="text-lg font-medium text-black dark:text-zinc-50">
                    {product.name}
                    <span className="ml-2 text-sm text-zinc-500">
                      ({product.unit})
                    </span>
                  </h2>
                  <span className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                    최저 {cheapest.price.toLocaleString()}원 · {cheapest.market_name}
                  </span>
                </div>
                <ul className="mt-3 flex flex-col gap-1 text-sm text-zinc-600 dark:text-zinc-400">
                  {rest.map((offer) => (
                    <li key={offer.market_id} className="flex justify-between">
                      <span>{offer.market_name}</span>
                      <span>{offer.price.toLocaleString()}원</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}
